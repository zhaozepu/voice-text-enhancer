#!/usr/bin/env python3
"""
本地预览通知动效 - 无需打包

直接生成一个可视化的 HTML 文件并用浏览器打开。
四宫格分别用不同背景对比效果，动画自动显示并居中。
"""
import re
import sys
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.notification_helper import get_html


def main():
    raw = get_html('{}')

    # 抽取 <style>...</style> 和 <body>...</body>，重新组装成预览页
    style_match = re.search(r'<style>(.*?)</style>', raw, re.S)
    body_match = re.search(r'<body>(.*?)</body>', raw, re.S)
    if not style_match or not body_match:
        print('解析 helper HTML 失败', file=sys.stderr)
        sys.exit(1)

    inner_style = style_match.group(1)
    # body 内只取 .anim-box 的 div 结构
    inner_body_match = re.search(r'<div class="anim-box".*?</div>\s*</div>', body_match.group(1), re.S)
    inner_body = inner_body_match.group(0) if inner_body_match else body_match.group(1)

    # 在预览页中改写 .anim-box：让它自动显示、居中（不要 fixed 到顶部）
    override = """
    .preview-cell .anim-box {
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        opacity: 1 !important;
    }
    """

    cells = [
        ("纯黑（暗色桌面）",  "#111",                                                           '#fff'),
        ("纯白（亮色桌面）",  "#f5f5f7",                                                        '#222'),
        ("深色渐变",          "linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%)",   '#fff'),
        ("彩色渐变",          "linear-gradient(135deg,#ffd6e0 0%,#c8e6ff 50%,#d8f3dc 100%)",   '#222'),
    ]

    cell_html = "\n".join(
        f'''<div class="preview-cell" style="background:{bg};color:{fg};">
              <div class="label">{label}</div>
              {inner_body}
            </div>'''
        for label, bg, fg in cells
    )

    preview = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>动效预览</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 100%; height: 100%; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
  .grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    width: 100vw; height: 100vh;
  }}
  .preview-cell {{ position: relative; overflow: hidden; }}
  .preview-cell .label {{
    position: absolute; top: 12px; left: 16px;
    font-size: 12px; font-weight: 600; padding: 4px 10px;
    border-radius: 12px; background: rgba(0,0,0,0.35); color: inherit;
    z-index: 10;
  }}
  {inner_style}
  {override}
</style>
</head>
<body>
<div class="grid">
{cell_html}
</div>
</body>
</html>
"""

    out = Path(tempfile.gettempdir()) / 'vte_anim_preview.html'
    out.write_text(preview, encoding='utf-8')
    print(f"已生成预览: {out}")
    subprocess.run(['open', str(out)])


if __name__ == '__main__':
    main()
