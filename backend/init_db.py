"""
数据库初始化脚本
用于从项目根目录初始化数据库
"""
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import init_db

if __name__ == "__main__":
    try:
        print("正在初始化数据库...")
        init_db()
        print("✓ 数据库初始化成功")
        sys.exit(0)
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        sys.exit(1)
