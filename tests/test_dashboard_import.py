#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\military-Rural Revitalization-system\backend')

try:
    from app.api.v1.data import dashboard
    print(f"[OK] dashboard 模块导入成功")
    print(f"  router: {dashboard.router}")
    print(f"  prefix: {dashboard.router.prefix}")
except Exception as e:
    print(f"[FAIL] dashboard 模块导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.api.v1.data import router as data_router
    print(f"\n[OK] data 子模块导入成功")
    print(f"  router: {data_router}")

    # 检查包含的路由
    print(f"\n包含的路由:")
    for route in data_router.routes:
        print(f"  - {route.path}")
except Exception as e:
    print(f"\n[FAIL] data 子模块导入失败: {e}")
    import traceback
    traceback.print_exc()
