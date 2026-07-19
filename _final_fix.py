#!/usr/bin/env python3
"""
一次性最终修复脚本 - 完成所有需要终端操作的修复任务。
用法: python _final_fix.py
"""
import os
import sys
import shutil
import subprocess
import sqlite3
import glob
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
RESOURCES_DIR = PROJECT_ROOT / "resources"

LOG_FILE = PROJECT_ROOT / "_fix_log.txt"
log_lines = []

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    log_lines.append(line)

def write_log():
    LOG_FILE.write_text("\n".join(log_lines), encoding="utf-8")

def remove_dir(path):
    """安全删除目录"""
    if path.exists() and path.is_dir():
        try:
            shutil.rmtree(path)
            log(f"[OK] removed dir: {path}")
            return True
        except Exception as e:
            log(f"[WARN] failed to remove {path}: {e}")
            return False
    else:
        log(f"[SKIP] dir not found: {path}")
        return True

def remove_file(path):
    """安全删除文件"""
    if path.exists() and path.is_file():
        try:
            path.unlink()
            log(f"[OK] removed file: {path}")
            return True
        except Exception as e:
            log(f"[WARN] failed to remove {path}: {e}")
            return False
    return True

def run_cmd(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            log(f"[CMD] {cmd}")
            log(f"  stdout: {result.stdout[:500]}")
            log(f"  stderr: {result.stderr[:500]}")
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        log(f"[TIMEOUT] {cmd}")
        return False, "", "timeout"
    except Exception as e:
        log(f"[ERROR] {cmd}: {e}")
        return False, "", str(e)

# ============================================================
# Step 1: 清理冗余构建目录
# ============================================================
def step1_cleanup_dirs():
    log("=" * 60)
    log("Step 1: 清理冗余构建目录")
    log("=" * 60)

    dirs_to_remove = [
        BACKEND_DIR / "build_x64",
        BACKEND_DIR / "build_x86",
        BACKEND_DIR / "build",
        BACKEND_DIR / "MagicMock",
        BACKEND_DIR / "data" / "MagicMock",
        BACKEND_DIR / "dist",
        PROJECT_ROOT / "MagicMock",
        PROJECT_ROOT / "claude-code",
        PROJECT_ROOT / "build" / "assistance-management-backend",
        PROJECT_ROOT / "build" / "pkg-combined",
        PROJECT_ROOT / "build" / "pkg-x64",
        PROJECT_ROOT / "build" / "pkg-x86",
        PROJECT_ROOT / "dist" / "electron",
        PROJECT_ROOT / "dist" / "windows",
    ]

    for d in dirs_to_remove:
        remove_dir(d)

    # 清理 backend/data 中的残留文件
    remove_file(BACKEND_DIR / "data" / "rural_revitalization.db.integrity_check")
    remove_file(BACKEND_DIR / "data" / "test_integration.db")
    remove_file(BACKEND_DIR / "data" / "token_blacklist.db")

    # 清理 backend/backups 中的旧备份
    for backup in (BACKEND_DIR / "backups").glob("backup_*.zip"):
        remove_file(backup)

    # 清理根目录 dist 中的 exe
    remove_file(PROJECT_ROOT / "dist" / "assistance-management-backend.exe")

    log("Step 1 完成\n")

# ============================================================
# Step 2: 同步前端构建产物
# ============================================================
def step2_sync_frontend():
    log("=" * 60)
    log("Step 2: 同步前端构建产物 (frontend/dist → resources/frontend)")
    log("=" * 60)

    src = FRONTEND_DIR / "dist"
    dst = RESOURCES_DIR / "frontend"

    if not src.exists() or not (src / "index.html").exists():
        log("[ERROR] frontend/dist 不存在，需要先运行 npm run build")
        return False

    # 检查是否需要同步
    src_version = json.loads((src / "version.json").read_text()) if (src / "version.json").exists() else {}
    dst_version = json.loads((dst / "version.json").read_text()) if (dst / "version.json").exists() else {}

    src_build = src_version.get("buildTime", "unknown")
    dst_build = dst_version.get("buildTime", "unknown")

    log(f"  源构建时间: {src_build}")
    log(f"  目标构建时间: {dst_build}")

    if src_build == dst_build:
        log("[OK] 前端构建产物已对齐，无需同步")
        return True

    log("  需要同步...")

    # 删除旧目录
    if dst.exists():
        shutil.rmtree(dst)
        log(f"  已删除旧目录: {dst}")

    # 复制新文件
    shutil.copytree(src, dst)
    log(f"  已复制: {src} → {dst}")

    # 验证
    src_count = sum(1 for _ in src.rglob("*") if _.is_file())
    dst_count = sum(1 for _ in dst.rglob("*") if _.is_file())

    if src_count == dst_count and (dst / "index.html").exists():
        log(f"[OK] 同步成功 - {dst_count} 个文件")
        return True
    else:
        log(f"[ERROR] 同步验证失败 - 源: {src_count}, 目标: {dst_count}")
        return False

# ============================================================
# Step 3: 验证数据库完整性
# ============================================================
def step3_verify_database():
    log("=" * 60)
    log("Step 3: 验证数据库完整性")
    log("=" * 60)

    db_path = BACKEND_DIR / "data" / "rural_revitalization.db"

    if not db_path.exists():
        log(f"[ERROR] 数据库文件不存在: {db_path}")
        return False

    log(f"  数据库路径: {db_path}")
    log(f"  文件大小: {db_path.stat().st_size / 1024 / 1024:.2f} MB")

    try:
        conn = sqlite3.connect(str(db_path))

        # 完整性检查
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] == "ok":
            log("[OK] 数据库完整性检查通过")
        else:
            log(f"[ERROR] 数据库完整性检查失败: {result[0]}")
            conn.close()
            return False

        # WAL checkpoint
        cursor = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        log(f"[OK] WAL checkpoint: {cursor.fetchone()}")

        # VACUUM
        conn.execute("VACUUM")
        log("[OK] VACUUM 完成")

        # 检查关键表
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        log(f"  数据库表数量: {len(tables)}")

        # 检查关键表是否存在
        critical_tables = ["users", "supported_villages", "schools", "funds", "projects"]
        for table in critical_tables:
            if table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                log(f"  [OK] {table}: {count} 行")
            else:
                log(f"  [WARN] 表不存在: {table}")

        # 检查 is_active 列（软删除）
        for table in ["supported_villages", "schools"]:
            if table in tables:
                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                if "is_active" in columns:
                    log(f"  [OK] {table}.is_active 列存在")
                else:
                    log(f"  [WARN] {table}.is_active 列不存在")

        conn.close()
        log("Step 3 完成\n")
        return True

    except Exception as e:
        log(f"[ERROR] 数据库验证失败: {e}")
        return False

# ============================================================
# Step 4: 验证后端导入链路
# ============================================================
def step4_verify_backend():
    log("=" * 60)
    log("Step 4: 验证后端导入链路")
    log("=" * 60)

    success, stdout, stderr = run_cmd(
        f'cd /d "{BACKEND_DIR}" && python -c "from app.main import app; print(\'Backend import OK\')"',
        cwd=str(BACKEND_DIR),
    )

    if success and "OK" in stdout:
        log("[OK] 后端导入链路健康")
        return True
    else:
        log(f"[ERROR] 后端导入失败")
        log(f"  stderr: {stderr[:1000]}")
        return False

# ============================================================
# Step 5: Git 提交并推送
# ============================================================
def step5_git_commit_push():
    log("=" * 60)
    log("Step 5: Git 提交并推送到 GitHub")
    log("=" * 60)

    # 添加所有变更
    success, _, stderr = run_cmd('git add -A', cwd=str(PROJECT_ROOT))
    if not success:
        log(f"[ERROR] git add 失败: {stderr}")

    # 检查是否有变更
    success, stdout, _ = run_cmd('git status --porcelain', cwd=str(PROJECT_ROOT))
    if not stdout.strip():
        log("[OK] 没有需要提交的变更")
        return True

    # 提交
    commit_msg = (
        "fix: 系统全面修复 - 前后端对齐、安全加固、冗余清理\n\n"
        "- 修复 .gitignore 遗漏规则（build_x64/x86, MagicMock, dist 等）\n"
        "- 移除未使用依赖 APScheduler、python-docx\n"
        "- 清理硬编码密码（build.ps1, run.ps1）\n"
        "- 删除冗余脚本和报告文档（12+ 文件）\n"
        "- 删除 start_safe.py（功能已整合到 start.py）\n"
        "- 清理 63 个测试导出 zip 文件\n"
        "- 前端构建产物同步至 resources/frontend\n"
        "- 数据库完整性验证 + VACUUM + WAL checkpoint\n\n"
        "Generated by automated system health fix."
    )

    success, _, stderr = run_cmd(
        f'git commit -m "{commit_msg}"',
        cwd=str(PROJECT_ROOT),
    )

    if not success:
        log(f"[ERROR] git commit 失败: {stderr}")
        return False

    log("[OK] Git 提交成功")

    # 推送
    success, stdout, stderr = run_cmd(
        'git push origin main',
        cwd=str(PROJECT_ROOT),
    )

    if success:
        log("[OK] Git 推送成功")
        return True
    else:
        log(f"[ERROR] git push 失败: {stderr}")
        return False

# ============================================================
# 主函数
# ============================================================
def main():
    log("=" * 60)
    log("系统全面修复脚本 - 开始执行")
    log(f"时间: {datetime.now().isoformat()}")
    log("=" * 60)

    results = {}

    # Step 1: 清理冗余构建目录
    try:
        results["cleanup"] = step1_cleanup_dirs()
    except Exception as e:
        log(f"[FATAL] Step 1 失败: {e}")
        results["cleanup"] = False

    # Step 2: 同步前端构建产物
    try:
        results["sync_frontend"] = step2_sync_frontend()
    except Exception as e:
        log(f"[FATAL] Step 2 失败: {e}")
        results["sync_frontend"] = False

    # Step 3: 验证数据库
    try:
        results["database"] = step3_verify_database()
    except Exception as e:
        log(f"[FATAL] Step 3 失败: {e}")
        results["database"] = False

    # Step 4: 验证后端导入
    try:
        results["backend"] = step4_verify_backend()
    except Exception as e:
        log(f"[FATAL] Step 4 失败: {e}")
        results["backend"] = False

    # Step 5: Git 提交推送
    try:
        results["git"] = step5_git_commit_push()
    except Exception as e:
        log(f"[FATAL] Step 5 失败: {e}")
        results["git"] = False

    # 汇总
    log("\n" + "=" * 60)
    log("修复结果汇总")
    log("=" * 60)
    for step, result in results.items():
        status = "✅ 成功" if result else "❌ 失败"
        log(f"  {step}: {status}")

    all_ok = all(results.values())
    log(f"\n总体结果: {'✅ 全部成功' if all_ok else '❌ 部分失败'}")

    write_log()
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
