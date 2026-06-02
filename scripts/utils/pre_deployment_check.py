#!/usr/bin/env python3
"""
部署前系统检查脚本
检查系统是否准备好部署打包
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# 检查结果
issues = {
    "critical": [],  # 严重问题 - 必须修复
    "warning": [],   # 警告 - 建议修复
    "info": []       # 信息 - 可选修复
}


def add_issue(level: str, category: str, message: str, fix: str = ""):
    """添加问题"""
    issues[level].append({
        "category": category,
        "message": message,
        "fix": fix
    })


def check_env_files():
    """检查环境变量文件"""
    print("\n[1/10] 检查环境变量配置...")

    # 检查 .env 文件
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        add_issue("critical", "配置", ".env 文件不存在", "从 .env.example 复制并配置")
        return

    # 检查关键配置
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()

    required_keys = [
        "SECRET_KEY",
        "DATABASE_URL",
        "CORS_ORIGINS"
    ]

    for key in required_keys:
        if key not in env_content:
            add_issue("critical", "配置", f"缺少必需的环境变量: {key}")

    # 检查 SECRET_KEY 长度
    if "SECRET_KEY=" in env_content:
        for line in env_content.split('\n'):
            if line.startswith("SECRET_KEY="):
                secret_key = line.split('=', 1)[1].strip()
                if len(secret_key) < 32:
                    add_issue("critical", "安全", "SECRET_KEY 长度不足（至少32字符）")

    # 检查 DEBUG 模式
    if "DEBUG=true" in env_content or "DEBUG=True" in env_content:
        add_issue("warning", "配置", "生产环境应关闭 DEBUG 模式", "设置 DEBUG=false")

    print("  [OK] 环境变量配置检查完成")


def check_database():
    """检查数据库"""
    print("\n[2/10] 检查数据库...")

    db_file = PROJECT_ROOT / "data" / "rural_revitalization.db"
    if not db_file.exists():
        add_issue("warning", "数据库", "数据库文件不存在，首次运行时会自动创建")
    else:
        # 检查数据库大小
        db_size = db_file.stat().st_size
        if db_size == 0:
            add_issue("warning", "数据库", "数据库文件为空")
        else:
            print(f"  [OK] 数据库文件大小: {db_size / 1024 / 1024:.2f} MB")

    # 检查数据目录
    data_dir = PROJECT_ROOT / "data"
    if not data_dir.exists():
        add_issue("warning", "数据库", "data 目录不存在", "创建 data 目录")

    print("  [OK] 数据库检查完成")


def check_dependencies():
    """检查依赖包"""
    print("\n[3/10] 检查依赖包...")

    # 检查后端依赖
    requirements_file = BACKEND_DIR / "requirements.txt"
    if not requirements_file.exists():
        add_issue("critical", "依赖", "backend/requirements.txt 不存在")

    # 检查前端依赖
    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        add_issue("critical", "依赖", "frontend/package.json 不存在")
    else:
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            add_issue("warning", "依赖", "前端依赖未安装", "运行 npm install")

    print("  [OK] 依赖包检查完成")


def check_security():
    """检查安全配置"""
    print("\n[4/10] 检查安全配置...")

    # 检查 .gitignore
    gitignore = PROJECT_ROOT / ".gitignore"
    if gitignore.exists():
        with open(gitignore, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()

        security_patterns = [".env", "*.db", "*.key", "secrets/"]
        for pattern in security_patterns:
            if pattern not in gitignore_content:
                add_issue("warning", "安全", f".gitignore 中缺少: {pattern}")

    # 检查敏感文件
    sensitive_files = [
        ".env",
        "backend/secrets/master.key",
        "backend/secrets/encrypted_config.json"
    ]

    for file_path in sensitive_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            # 检查文件权限（Windows 上跳过）
            if sys.platform != "win32":
                stat_info = full_path.stat()
                if stat_info.st_mode & 0o077:
                    add_issue("warning", "安全", f"{file_path} 权限过于宽松", "chmod 600")

    print("  [OK] 安全配置检查完成")


def check_api_routes():
    """检查 API 路由"""
    print("\n[5/10] 检查 API 路由...")

    api_init = BACKEND_DIR / "app" / "api" / "v1" / "__init__.py"
    if not api_init.exists():
        add_issue("critical", "API", "API 路由初始化文件不存在")
        return

    # 检查路由模块
    with open(api_init, 'r', encoding='utf-8') as f:
        content = f.read()

    if "_ROUTE_MODULES" not in content:
        add_issue("warning", "API", "未找到路由模块列表")

    print("  [OK] API 路由检查完成")


def check_frontend_build():
    """检查前端构建配置"""
    print("\n[6/10] 检查前端构建配置...")

    # 检查 vite.config.ts
    vite_config = FRONTEND_DIR / "vite.config.ts"
    if not vite_config.exists():
        add_issue("critical", "前端", "vite.config.ts 不存在")

    # 检查 tsconfig.json
    tsconfig = FRONTEND_DIR / "tsconfig.json"
    if not tsconfig.exists():
        add_issue("warning", "前端", "tsconfig.json 不存在")

    print("  [OK] 前端构建配置检查完成")


def check_static_files():
    """检查静态文件"""
    print("\n[7/10] 检查静态文件...")

    # 检查上传目录
    uploads_dir = PROJECT_ROOT / "uploads"
    if not uploads_dir.exists():
        add_issue("info", "文件", "uploads 目录不存在，首次运行时会自动创建")

    # 检查日志目录
    logs_dir = PROJECT_ROOT / "logs"
    if not logs_dir.exists():
        add_issue("info", "文件", "logs 目录不存在，首次运行时会自动创建")

    print("  [OK] 静态文件检查完成")


def check_cors_config():
    """检查 CORS 配置"""
    print("\n[8/10] 检查 CORS 配置...")

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()

        if "CORS_ORIGINS=" in env_content:
            for line in env_content.split('\n'):
                if line.startswith("CORS_ORIGINS="):
                    origins = line.split('=', 1)[1].strip()
                    if "*" in origins:
                        add_issue("critical", "安全", "CORS 配置允许所有来源（*），生产环境不安全")
                    elif "localhost" in origins or "127.0.0.1" in origins:
                        add_issue("info", "配置", "CORS 配置包含 localhost，生产环境可能需要调整")

    print("  [OK] CORS 配置检查完成")


def check_logging():
    """检查日志配置"""
    print("\n[9/10] 检查日志配置...")

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()

        if "LOG_LEVEL=DEBUG" in env_content:
            add_issue("warning", "配置", "生产环境建议使用 INFO 或 WARNING 日志级别")

    print("  [OK] 日志配置检查完成")


def check_ports():
    """检查端口配置"""
    print("\n[10/10] 检查端口配置...")

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()

        # 检查端口配置
        if "PORT=" in env_content:
            for line in env_content.split('\n'):
                if line.startswith("PORT="):
                    port = line.split('=', 1)[1].strip()
                    try:
                        port_num = int(port)
                        if port_num < 1024:
                            add_issue("warning", "配置", f"端口 {port_num} 需要管理员权限")
                    except ValueError:
                        add_issue("warning", "配置", f"无效的端口配置: {port}")

    print("  [OK] 端口配置检查完成")


def print_summary():
    """打印检查摘要"""
    print("\n" + "=" * 80)
    print("检查摘要")
    print("=" * 80)

    total_issues = len(issues["critical"]) + len(issues["warning"]) + len(issues["info"])

    if total_issues == 0:
        print("\n[OK] 未发现问题，系统准备就绪！")
        return True

    # 严重问题
    if issues["critical"]:
        print(f"\n[严重] 发现 {len(issues['critical'])} 个严重问题（必须修复）:")
        for i, issue in enumerate(issues["critical"], 1):
            print(f"\n  {i}. [{issue['category']}] {issue['message']}")
            if issue['fix']:
                print(f"     修复: {issue['fix']}")

    # 警告
    if issues["warning"]:
        print(f"\n[警告] 发现 {len(issues['warning'])} 个警告（建议修复）:")
        for i, issue in enumerate(issues["warning"], 1):
            print(f"\n  {i}. [{issue['category']}] {issue['message']}")
            if issue['fix']:
                print(f"     修复: {issue['fix']}")

    # 信息
    if issues["info"]:
        print(f"\n[信息] {len(issues['info'])} 条提示信息:")
        for i, issue in enumerate(issues["info"], 1):
            print(f"  {i}. [{issue['category']}] {issue['message']}")

    print("\n" + "=" * 80)

    if issues["critical"]:
        print("\n[失败] 存在严重问题，不建议部署")
        return False
    elif issues["warning"]:
        print("\n[警告] 存在警告，建议修复后再部署")
        return True
    else:
        print("\n[OK] 系统准备就绪")
        return True


def main():
    """主函数"""
    print("=" * 80)
    print("部署前系统检查")
    print("=" * 80)

    # 执行所有检查
    check_env_files()
    check_database()
    check_dependencies()
    check_security()
    check_api_routes()
    check_frontend_build()
    check_static_files()
    check_cors_config()
    check_logging()
    check_ports()

    # 打印摘要
    success = print_summary()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
