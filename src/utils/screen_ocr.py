"""
全屏截图 + macOS Vision 框架本地 OCR

完全离线、无需调用任何视觉模型。
依赖：pyobjc (Quartz, Vision, Foundation, AppKit)
"""
import os
import time
import tempfile
import subprocess
from pathlib import Path
from typing import List, Tuple
from loguru import logger


class ScreenCaptureError(RuntimeError):
    """截屏失败（通常是缺少屏幕录制权限）"""


def capture_screen() -> str:
    """
    使用 macOS 系统命令 screencapture 截取整个屏幕。
    返回 PNG 文件路径（位于临时目录），调用方负责清理。
    """
    fd, path = tempfile.mkstemp(prefix='vte_shot_', suffix='.png')
    os.close(fd)
    # -x 静音, 默认主屏全屏
    result = subprocess.run(
        ['screencapture', '-x', path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0 or not os.path.exists(path) or os.path.getsize(path) == 0:
        try:
            os.unlink(path)
        except Exception:
            pass
        msg = (result.stderr or '').strip() or f'screencapture 退出码 {result.returncode}'
        raise ScreenCaptureError(f"截屏失败: {msg}（请在系统设置 → 隐私与安全性 → 屏幕录制 中授权 润色）")
    return path


def has_screen_recording_permission() -> bool:
    """
    检查当前进程是否有屏幕录制权限（不会触发权限请求弹窗）。
    通过尝试一次零字节截屏判断。
    """
    fd, path = tempfile.mkstemp(prefix='vte_check_', suffix='.png')
    os.close(fd)
    try:
        result = subprocess.run(
            ['screencapture', '-x', '-t', 'png', path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0 and os.path.getsize(path) > 0
    except Exception:
        return False
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def ocr_image(image_path: str, langs: List[str] = None) -> str:
    """
    使用 macOS Vision 框架对图片做 OCR，按从上到下、从左到右拼接所有文本。

    Args:
        image_path: 图片路径
        langs: 识别语言代码列表，默认 ['zh-Hans', 'en-US']

    Returns:
        识别出的所有文本，多段用换行分隔
    """
    if langs is None:
        langs = ['zh-Hans', 'en-US']

    try:
        from Foundation import NSURL
        from Vision import (
            VNRecognizeTextRequest,
            VNImageRequestHandler,
            VNRequestTextRecognitionLevelAccurate,
        )
    except ImportError as e:
        logger.error(f"Vision 框架不可用，请确保已安装 pyobjc-framework-Vision: {e}")
        raise

    url = NSURL.fileURLWithPath_(image_path)
    handler = VNImageRequestHandler.alloc().initWithURL_options_(url, None)

    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    try:
        request.setRecognitionLanguages_(langs)
    except Exception:
        pass

    success, error = handler.performRequests_error_([request], None)
    if not success:
        logger.error(f"Vision OCR 失败: {error}")
        return ""

    results = request.results() or []

    # 收集 (y_top, x_left, text)，再按行排序拼接
    # bbox 是 normalized，原点在左下，y 越大越靠上 → 取 1-y 作为"从上往下"序号
    items: List[Tuple[float, float, str]] = []
    for obs in results:
        candidates = obs.topCandidates_(1)
        if not candidates:
            continue
        text = str(candidates[0].string())
        if not text.strip():
            continue
        bbox = obs.boundingBox()
        # bbox.origin.y + bbox.size.height 是矩形顶端的 y（normalized）
        y_top = 1.0 - (bbox.origin.y + bbox.size.height)
        x_left = bbox.origin.x
        items.append((y_top, x_left, text))

    if not items:
        return ""

    # 简易行聚合：y 差小于 0.01 视为同一行
    items.sort(key=lambda t: (t[0], t[1]))
    lines: List[List[Tuple[float, float, str]]] = []
    LINE_THRESHOLD = 0.012
    for item in items:
        if lines and abs(item[0] - lines[-1][-1][0]) < LINE_THRESHOLD:
            lines[-1].append(item)
        else:
            lines.append([item])

    # 每行内按 x 排序、用空格连接
    out_lines = []
    for line in lines:
        line.sort(key=lambda t: t[1])
        out_lines.append(' '.join(t[2] for t in line))

    return '\n'.join(out_lines)


def capture_and_ocr() -> Tuple[str, str]:
    """
    截屏 + OCR 一站式接口。

    Returns:
        (ocr_text, screenshot_path)
        调用方使用完后应自行删除 screenshot_path 以避免残留
    """
    t0 = time.time()
    path = capture_screen()
    logger.info(f"截屏完成: {path}, 耗时 {time.time() - t0:.2f}s")

    t1 = time.time()
    text = ocr_image(path)
    logger.info(f"OCR 完成: {len(text)} 字符, 耗时 {time.time() - t1:.2f}s")

    return text, path
