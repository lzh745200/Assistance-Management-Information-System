#!/usr/bin/env python3
"""
创建圆形图标脚本
从方形图标 bz.png 创建圆形版本
"""

from PIL import Image, ImageDraw
import os

def create_circle_mask(size):
    """创建圆形蒙版"""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    return mask

def create_circle_icon(input_path, output_path, size=None):
    """创建圆形图标"""
    # 打开原始图像
    img = Image.open(input_path).convert('RGBA')

    # 如果指定了尺寸，调整图像大小
    if size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    else:
        size = img.size[0]

    # 创建圆形蒙版
    mask = create_circle_mask(size)

    # 创建输出图像
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0))
    output.putalpha(mask)

    # 保存
    output.save(output_path, 'PNG')
    print(f"已创建: {output_path} ({size}x{size})")

def create_ico_file(png_files, output_path):
    """从多个 PNG 文件创建 ICO 文件"""
    # 只使用较小的尺寸创建 ICO，因为大尺寸可能导致问题
    # electron-builder 需要至少 256x256
    target_sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in target_sizes:
        png_file = None
        for pf in png_files:
            if f"icon_{size}x{size}.png" in pf:
                png_file = pf
                break

        if png_file and os.path.exists(png_file):
            img = Image.open(png_file)
            images.append(img)
            print(f"  添加尺寸: {size}x{size}")

    if images:
        # 保存为 ICO，明确指定所有尺寸
        images[0].save(
            output_path,
            format='ICO',
            sizes=[(img.size[0], img.size[1]) for img in images],
            append_images=images[1:]
        )
        print(f"已创建 ICO: {output_path}")
        print(f"  总共包含 {len(images)} 个尺寸")

def main():
    # 路径配置
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, 'frontend', 'public', 'images', 'biaozhi', 'bz.png')
    output_dir = os.path.join(base_dir, 'resources', 'icons')
    circle_dir = os.path.join(output_dir, 'circle')

    # 确保输出目录存在
    os.makedirs(circle_dir, exist_ok=True)

    print("=" * 50)
    print("创建圆形图标")
    print("=" * 50)
    print(f"输入文件: {input_file}")
    print(f"输出目录: {output_dir}")
    print()

    # 创建主圆形图标 (1280x1280)
    main_circle = os.path.join(output_dir, 'bz-circle.png')
    create_circle_icon(input_file, main_circle)

    # 创建多尺寸圆形图标
    sizes = [16, 32, 48, 64, 128, 256, 512]
    png_files = []

    print()
    print("创建多尺寸图标:")
    for size in sizes:
        output_file = os.path.join(circle_dir, f'icon_{size}x{size}.png')
        create_circle_icon(input_file, output_file, size)
        png_files.append(output_file)

    # 创建 ICO 文件
    print()
    print("创建 Windows ICO 文件:")
    ico_file = os.path.join(output_dir, 'app-circle.ico')
    create_ico_file(png_files, ico_file)

    print()
    print("=" * 50)
    print("完成！")
    print("=" * 50)
    print()
    print("生成的文件:")
    print(f"  - {main_circle}")
    print(f"  - {ico_file}")
    print(f"  - {circle_dir}/*.png ({len(sizes)} 个尺寸)")

if __name__ == '__main__':
    main()
