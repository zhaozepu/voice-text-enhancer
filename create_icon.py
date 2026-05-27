#!/usr/bin/env python3
"""
创建应用图标
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """创建应用图标"""
    # 创建一个 1024x1024 的图标（macOS 推荐尺寸）
    size = 1024
    img = Image.new('RGB', (size, size), color='#4A90E2')
    draw = ImageDraw.Draw(img)

    # 绘制圆角矩形背景
    radius = 180
    draw.rounded_rectangle(
        [(80, 80), (size-80, size-80)],
        radius=radius,
        fill='#2E5C8A'
    )

    # 绘制文字 "T"
    try:
        font_size = 500
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()

    # 居中绘制文字
    text = "✨"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 50

    draw.text((x, y), text, fill='white', font=font)

    # 保存为 PNG
    png_path = 'icon.png'
    img.save(png_path)
    print(f"✓ 图标已创建: {png_path}")

    # 创建 iconset 目录
    iconset_dir = 'icon.iconset'
    if not os.path.exists(iconset_dir):
        os.makedirs(iconset_dir)

    # 生成不同尺寸的图标
    sizes = [16, 32, 128, 256, 512, 1024]
    for s in sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(f'{iconset_dir}/icon_{s}x{s}.png')
        if s <= 512:  # @2x 版本
            resized_2x = img.resize((s*2, s*2), Image.Resampling.LANCZOS)
            resized_2x.save(f'{iconset_dir}/icon_{s}x{s}@2x.png')

    print(f"✓ Iconset 已创建: {iconset_dir}")
    return iconset_dir

if __name__ == '__main__':
    create_icon()
    print("\n下一步：运行以下命令转换为 .icns:")
    print("iconutil -c icns icon.iconset")
