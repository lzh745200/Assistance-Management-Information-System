"""
测试加密密钥加载
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 设置环境变量启用加密密钥
os.environ["USE_ENCRYPTED_SECRETS"] = "true"

from backend.app.core.config import settings

print("=" * 60)
print("测试加密密钥加载")
print("=" * 60)
print()

print(f"USE_ENCRYPTED_SECRETS: {settings.USE_ENCRYPTED_SECRETS}")
print(f"SECRET_KEY 长度: {len(settings.SECRET_KEY)}")
print(f"SECRET_KEY 前10位: {settings.SECRET_KEY[:10]}...")
print(f"CSRF_SECRET_KEY 长度: {len(settings.CSRF_SECRET_KEY)}")
print(f"CSRF_SECRET_KEY 前10位: {settings.CSRF_SECRET_KEY[:10]}...")
print()

# 验证密钥是否正确加载
if settings.SECRET_KEY and len(settings.SECRET_KEY) > 32:
    print("[OK] SECRET_KEY 加载成功")
else:
    print("[FAIL] SECRET_KEY 加载失败")
    sys.exit(1)

if settings.CSRF_SECRET_KEY and len(settings.CSRF_SECRET_KEY) > 32:
    print("[OK] CSRF_SECRET_KEY 加载成功")
else:
    print("[FAIL] CSRF_SECRET_KEY 加载失败")
    sys.exit(1)

print()
print("=" * 60)
print("测试通过！")
print("=" * 60)
