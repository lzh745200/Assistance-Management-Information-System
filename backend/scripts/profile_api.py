"""
API 性能 Profiling 脚本

使用 cProfile 对指定 API 端点进行性能剖析，输出火焰图数据。

Usage:
    # 对单个端点进行 100 次请求的性能分析
    python scripts/profile_api.py --endpoint /api/v1/supported-villages --count 100

    # 批量压测多个核心端点
    python scripts/profile_api.py --batch --count 50

    # 生成 pstats 报告（可导入 snakeviz 可视化）
    python scripts/profile_api.py --endpoint /api/v1/funds/analysis --output profile_funds.pstats
"""

import argparse
import cProfile
import json
import pstats
import sys
import time
from io import StringIO
from pathlib import Path

# 确保 backend 在 path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

# 核心端点（覆盖所有模块）
CORE_ENDPOINTS = [
    # 系统
    ("GET", "/api/v1/system/health"),
    ("GET", "/api/v1/system/status"),
    # 帮扶村
    ("GET", "/api/v1/supported-villages?page=1&page_size=50"),
    ("GET", "/api/v1/supported-villages/1"),
    # 学校
    ("GET", "/api/v1/schools?page=1&page_size=50"),
    ("GET", "/api/v1/schools/1"),
    # 项目
    ("GET", "/api/v1/projects?page=1&page_size=50"),
    ("GET", "/api/v1/projects/1"),
    # 资金
    ("GET", "/api/v1/funds?page=1&page_size=50"),
    ("GET", "/api/v1/funds/statistics/overview"),
    # 政策
    ("GET", "/api/v1/policies?page=1&page_size=50"),
    # 审批
    ("GET", "/api/v1/approval/tasks?status=pending"),
    # 组织
    ("GET", "/api/v1/organizations/tree"),
    # 数据分析
    ("GET", "/api/v1/data/dashboard/overview"),
    ("GET", "/api/v1/data/statistics/village"),
    # 地图
    ("GET", "/api/v1/map/tiles?z=5&x=10&y=10"),
    # 全文搜索
    ("GET", "/api/v1/search?q=村"),
]


def profile_endpoint(method: str, path: str, count: int = 100) -> dict:
    """对单个端点进行 cProfile 分析"""
    profiler = cProfile.Profile()

    def _request():
        if method == "GET":
            client.get(path)
        elif method == "POST":
            client.post(path, json={})

    profiler.enable()
    start = time.perf_counter()
    for _ in range(count):
        _request()
    wall_time = (time.perf_counter() - start) * 1000
    profiler.disable()

    # 生成统计
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumtime")
    stats.print_stats(20)  # top 20 函数

    return {
        "method": method,
        "path": path,
        "count": count,
        "total_wall_ms": round(wall_time, 1),
        "avg_ms": round(wall_time / count, 2),
        "top_functions": stream.getvalue(),
    }


def run_batch(count: int = 50) -> list:
    """批量分析所有核心端点"""
    results = []
    for method, path in CORE_ENDPOINTS:
        print(f"  Profiling {method} {path} ...")
        result = profile_endpoint(method, path, count)
        results.append({
            "method": result["method"],
            "path": result["path"],
            "avg_ms": result["avg_ms"],
            "total_wall_ms": result["total_wall_ms"],
        })
        # 标记慢端点
        if result["avg_ms"] > 500:
            print(f"    ⚠  SLOW: {result['avg_ms']}ms avg")
        else:
            print(f"    ✅ {result['avg_ms']}ms avg")
    return results


def save_pstats(endpoint: str, output: str, count: int = 100):
    """保存 cProfile 数据为 pstats 文件（可用 snakeviz 可视化）"""
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(count):
        client.get(endpoint)
    profiler.disable()
    profiler.dump_stats(output)
    print(f"pstats 已保存到 {output}")
    print("可视化: pip install snakeviz && snakeviz " + output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API Profiling Tool")
    parser.add_argument("--endpoint", type=str, help="单个 API 端点路径")
    parser.add_argument("--method", type=str, default="GET", help="HTTP 方法")
    parser.add_argument("--count", type=int, default=100, help="请求次数")
    parser.add_argument("--batch", action="store_true", help="批量分析所有核心端点")
    parser.add_argument("--output", type=str, help="pstats 输出文件路径")
    args = parser.parse_args()

    print("=" * 60)
    print("API 性能 Profiling")
    print("=" * 60)

    if args.batch:
        print(f"\n批量分析 {len(CORE_ENDPOINTS)} 个核心端点 (各 {args.count} 次请求)...\n")
        results = run_batch(args.count)
        print("\n--- 汇总（按平均响应时间排序）---")
        results.sort(key=lambda r: r["avg_ms"], reverse=True)
        for i, r in enumerate(results[:10], 1):
            flag = "⚠" if r["avg_ms"] > 500 else "✅"
            print(f"  {i:2}. {flag} {r['avg_ms']:7.1f}ms  {r['method']:4} {r['path']}")

    elif args.output:
        save_pstats(args.endpoint, args.output, args.count)

    elif args.endpoint:
        result = profile_endpoint(args.method, args.endpoint, args.count)
        print(f"\n端点: {args.method} {args.endpoint}")
        print(f"请求次数: {args.count}")
        print(f"总耗时: {result['total_wall_ms']}ms")
        print(f"平均: {result['avg_ms']}ms")
        print(f"\nTop 20 函数 (按累积时间):\n{result['top_functions']}")

    else:
        parser.print_help()
