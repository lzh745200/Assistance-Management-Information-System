#!/usr/bin/env python3
"""系统性能测试脚本

测试后端API性能和前端加载性能
"""

import time
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


def test_import_performance():
    """测试后端导入性能"""
    print("=" * 60)
    print("测试后端导入性能")
    print("=" * 60)

    start = time.time()
    from app.main import app
    from fastapi.routing import APIRoute

    routes = [r for r in app.routes if isinstance(r, APIRoute)]
    import_time = time.time() - start

    print(f"路由数量: {len(routes)}")
    print(f"导入耗时: {import_time:.2f}s")

    if import_time < 20:
        print("✓ 导入性能良好 (< 20s)")
    elif import_time < 30:
        print("⚠ 导入性能一般 (20-30s)")
    else:
        print("✗ 导入性能较差 (> 30s)")

    return import_time


def test_dashboard_api_performance():
    """测试仪表盘API性能"""
    print("\n" + "=" * 60)
    print("测试仪表盘API性能")
    print("=" * 60)

    from app.core.database import SessionLocal
    from app.api.v1.data.dashboard import (
        _query_village_stats,
        _query_fund_stats,
        _query_project_approval_stats,
    )
    from app.api.v1.data_scope import DataScope

    db = SessionLocal()
    data_scope = DataScope(is_admin=True, org_ids=[], user_id=1)

    # 测试 village stats
    start = time.time()
    village_stats = _query_village_stats(db, data_scope)
    village_time = time.time() - start
    print(f"Village stats: {village_time:.3f}s")

    # 测试 fund stats
    start = time.time()
    fund_stats = _query_fund_stats(db, data_scope)
    fund_time = time.time() - start
    print(f"Fund stats: {fund_time:.3f}s")

    # 测试 project stats
    start = time.time()
    project_stats = _query_project_approval_stats(db, data_scope)
    project_time = time.time() - start
    print(f"Project stats: {project_time:.3f}s")

    db.close()

    total_time = village_time + fund_time + project_time
    print(f"\n总查询时间: {total_time:.3f}s")

    if total_time < 1:
        print("✓ API性能良好 (< 1s)")
    elif total_time < 2:
        print("⚠ API性能一般 (1-2s)")
    else:
        print("✗ API性能较差 (> 2s)")

    return total_time


def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "=" * 60)
    print("测试缓存性能")
    print("=" * 60)

    from app.core.database import SessionLocal
    from app.api.v1.data.dashboard import _query_village_stats, _get_cached, _set_cached
    from app.api.v1.data_scope import DataScope

    db = SessionLocal()
    data_scope = DataScope(is_admin=True, org_ids=[], user_id=1)

    # 第一次查询（无缓存）
    start = time.time()
    result1 = _query_village_stats(db, data_scope)
    uncached_time = time.time() - start
    print(f"无缓存查询: {uncached_time:.3f}s")

    # 手动缓存
    _set_cached("test_key", result1, ttl=60)

    # 第二次查询（从缓存读取）
    start = time.time()
    cached = _get_cached("test_key")
    cached_time = time.time() - start
    print(f"缓存读取: {cached_time:.3f}s")

    db.close()

    if cached_time < 0.01:
        print("✓ 缓存性能良好 (< 10ms)")
    else:
        print("⚠ 缓存性能一般")

    return uncached_time, cached_time


def main():
    print("系统性能测试")
    print("=" * 60)

    results = {}

    try:
        results["import_time"] = test_import_performance()
    except Exception as e:
        print(f"导入性能测试失败: {e}")
        results["import_time"] = None

    try:
        results["api_time"] = test_dashboard_api_performance()
    except Exception as e:
        print(f"API性能测试失败: {e}")
        results["api_time"] = None

    try:
        results["cache_times"] = test_cache_performance()
    except Exception as e:
        print(f"缓存性能测试失败: {e}")
        results["cache_times"] = None

    # 汇总
    print("\n" + "=" * 60)
    print("性能测试汇总")
    print("=" * 60)

    if results["import_time"]:
        print(f"后端导入时间: {results['import_time']:.2f}s")
    if results["api_time"]:
        print(f"Dashboard API时间: {results['api_time']:.3f}s")
    if results["cache_times"]:
        print(f"缓存读取时间: {results['cache_times'][1]:.3f}s")

    print("\n性能优化建议:")
    print("1. 后端导入时间应控制在20秒以内")
    print("2. Dashboard API应控制在1秒以内")
    print("3. 缓存读取应在10毫秒以内")

    return 0


if __name__ == "__main__":
    sys.exit(main())
