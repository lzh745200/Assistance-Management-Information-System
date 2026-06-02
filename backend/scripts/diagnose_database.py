#!/usr/bin/env python3
"""
数据库诊断脚本
执行全面的数据库健康检查并生成报告
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect, event
from app.core.config import settings


def _configure_sqlite_pragmas(dbapi_conn, connection_record):
    """配置 SQLite PRAGMA 优化参数"""
    cursor = dbapi_conn.cursor()
    try:
        # WAL 模式：允许并发读 + 单写，提升并发性能
        cursor.execute("PRAGMA journal_mode=WAL")
        # NORMAL 同步模式：平衡性能与安全性（单机版推荐）
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 增大缓存：~64MB（单机版可用更多内存）
        cursor.execute("PRAGMA cache_size=-65536")
        # 临时表存内存：加速临时查询
        cursor.execute("PRAGMA temp_store=MEMORY")
        # 启用外键约束：确保数据完整性
        cursor.execute("PRAGMA foreign_keys=ON")
        # 设置 busy_timeout：避免 SQLITE_BUSY 错误（5秒超时）
        cursor.execute("PRAGMA busy_timeout=5000")
        # 优化 mmap_size：使用内存映射 I/O（256MB）
        cursor.execute("PRAGMA mmap_size=268435456")
    finally:
        cursor.close()


def diagnose_database():
    """执行数据库诊断"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "database_url": settings.DATABASE_URL.replace(settings.SECRET_KEY, "***") if hasattr(settings, 'SECRET_KEY') else settings.DATABASE_URL,
        "checks": {}
    }

    # 创�� engine 并应用 PRAGMA 配置
    engine = create_engine(settings.DATABASE_URL)

    # 只对 SQLite 数据库应用 PRAGMA 配置
    if settings.DATABASE_URL.startswith("sqlite"):
        event.listens_for(engine, "connect")(_configure_sqlite_pragmas)

    with engine.connect() as conn:
        # 1. 完整性检查
        print("执行完整性检查...")
        result = conn.execute(text('PRAGMA integrity_check'))
        integrity = [row[0] for row in result]
        report["checks"]["integrity"] = {
            "status": "pass" if integrity == ["ok"] else "fail",
            "details": integrity
        }

        # 2. 外键检查
        print("执行外键约束检查...")
        result = conn.execute(text('PRAGMA foreign_key_check'))
        fk_violations = list(result)
        report["checks"]["foreign_keys"] = {
            "status": "pass" if not fk_violations else "fail",
            "violations": len(fk_violations),
            "details": [dict(row._mapping) for row in fk_violations[:10]]  # 最多显示10条
        }

        # 3. 配置检查
        print("检查 PRAGMA 配置...")
        pragmas = {
            'journal_mode': 'wal',
            'synchronous': '1',  # NORMAL = 1
            'cache_size': '-65536',
            'temp_store': '2',  # MEMORY = 2
            'foreign_keys': '1',
            'mmap_size': '268435456'
        }

        config_issues = []
        for pragma, expected in pragmas.items():
            result = conn.execute(text(f'PRAGMA {pragma}'))
            actual = str(result.scalar())
            if actual != expected:
                config_issues.append({
                    "pragma": pragma,
                    "expected": expected,
                    "actual": actual
                })

        report["checks"]["configuration"] = {
            "status": "pass" if not config_issues else "warning",
            "issues": config_issues
        }

        # 4. 数据库统计
        print("收集数据库统计信息...")
        result = conn.execute(text('PRAGMA page_count'))
        page_count = result.scalar()
        result = conn.execute(text('PRAGMA page_size'))
        page_size = result.scalar()

        report["statistics"] = {
            "size_mb": round(page_count * page_size / (1024 * 1024), 2),
            "page_count": page_count,
            "page_size": page_size
        }

        # 5. 表统计
        result = conn.execute(text(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ))
        table_count = result.scalar()

        result = conn.execute(text(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        ))
        index_count = result.scalar()

        report["statistics"]["tables"] = table_count
        report["statistics"]["indexes"] = index_count

        # 6. 索引使用情况
        print("分析索引使用情况...")
        result = conn.execute(text(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' LIMIT 10"
        ))
        sample_indexes = [{"name": row[0], "table": row[1]} for row in result]
        report["statistics"]["sample_indexes"] = sample_indexes

    # 生成总体状态
    all_passed = all(
        check.get("status") in ["pass", "warning"]
        for check in report["checks"].values()
    )
    report["overall_status"] = "healthy" if all_passed else "unhealthy"

    # 生成建议
    recommendations = []
    if config_issues:
        recommendations.append("部分 PRAGMA 配置与预期不符,建议重启服务以应用配置")
    if fk_violations:
        recommendations.append(f"发现 {len(fk_violations)} 个外键约束违规,需要修复数据一致性")
    if integrity != ["ok"]:
        recommendations.append("数据库完整性检查失败,建议立即备份并修复")

    report["recommendations"] = recommendations if recommendations else ["数据库状态良好,无需特殊操作"]

    return report


if __name__ == "__main__":
    # 设置 UTF-8 输出编码
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("=" * 60)
    print("数据库诊断报告")
    print("=" * 60)
    print()

    try:
        report = diagnose_database()

        # 打印报告
        print(json.dumps(report, indent=2, ensure_ascii=False))

        # 保存报告
        output_file = Path(__file__).parent.parent / "database_diagnosis_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print()
        print(f"报告已保存到: {output_file}")
        print()
        print("总体状态:", "健康" if report["overall_status"] == "healthy" else "异常")
        print()
        print("建议:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

    except Exception as e:
        print(f"诊断失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
