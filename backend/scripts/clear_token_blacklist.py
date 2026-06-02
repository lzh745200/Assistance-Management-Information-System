#!/usr/bin/env python3
"""清空 Token 黑名单 - 解决 401 认证问题"""

import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.token_blacklist import token_blacklist

def clear_blacklist():
    """清空所有黑名单记录"""
    try:
        print("[INFO] 正在清空 Token 黑名单...")
        token_blacklist.clear_all()
        print("[OK] Token 黑名单已清空")
        print("[INFO] 所有现有 token 现在都可以正常使用")
        print("[INFO] 建议用户重新登录以获取新的 token 对")
        return True
    except Exception as e:
        print(f"[ERROR] 清空黑名单失败: {e}")
        return False

if __name__ == "__main__":
    print("Token 黑名单清理工具")
    print("=" * 50)
    if clear_blacklist():
        sys.exit(0)
    else:
        sys.exit(1)
