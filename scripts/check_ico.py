#!/usr/bin/env python3
"""
验证 ICO 文件内容
"""

from PIL import Image
import sys

def check_ico(ico_path):
    """检查 ICO 文件包含的尺寸"""
    try:
        img = Image.open(ico_path)
        print(f"ICO 文件: {ico_path}")
        print(f"格式: {img.format}")
        print(f"模式: {img.mode}")
        print(f"尺寸: {img.size}")

        # 尝试获取所有图标尺寸
        if hasattr(img, 'n_frames'):
            print(f"包含帧数: {img.n_frames}")
            for i in range(img.n_frames):
                img.seek(i)
                print(f"  帧 {i}: {img.size}")

        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == '__main__':
    ico_path = "resources/icons/app-circle.ico"
    check_ico(ico_path)
