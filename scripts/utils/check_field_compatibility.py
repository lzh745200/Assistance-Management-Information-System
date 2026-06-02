#!/usr/bin/env python3
"""
前后端字段匹配检查脚本
检查所有 API 接口的字段定义是否一致
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 后端 API 目录
BACKEND_API_DIR = PROJECT_ROOT / "backend" / "app" / "api" / "v1"

# 前端 API 目录
FRONTEND_API_DIR = PROJECT_ROOT / "frontend" / "src" / "api"

# 常见的字段映射问题
COMMON_FIELD_MAPPINGS = {
    "work_date": "log_date",
    "title": "content",
    "log_type": "category",
    "name": "full_name",
    "username": "user_name",
}


def extract_pydantic_fields(file_path: Path) -> Dict[str, Set[str]]:
    """从 Python 文件中提取 Pydantic 模型字段"""
    models = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配 Pydantic 模型定义
        model_pattern = r'class\s+(\w+)\(BaseModel\):(.*?)(?=class\s+\w+\(|@router|def\s+|$)'
        matches = re.finditer(model_pattern, content, re.DOTALL)

        for match in matches:
            model_name = match.group(1)
            model_body = match.group(2)

            # 提取字段名
            field_pattern = r'^\s+(\w+):\s+'
            fields = set(re.findall(field_pattern, model_body, re.MULTILINE))

            if fields:
                models[model_name] = fields

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return models


def extract_typescript_interfaces(file_path: Path) -> Dict[str, Set[str]]:
    """从 TypeScript 文件中提取接口字段"""
    interfaces = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配 TypeScript 接口定义
        interface_pattern = r'export\s+interface\s+(\w+)\s*\{(.*?)\}'
        matches = re.finditer(interface_pattern, content, re.DOTALL)

        for match in matches:
            interface_name = match.group(1)
            interface_body = match.group(2)

            # 提取字段名
            field_pattern = r'^\s+(\w+)[\?:]'
            fields = set(re.findall(field_pattern, interface_body, re.MULTILINE))

            if fields:
                interfaces[interface_name] = fields

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return interfaces


def check_field_compatibility(backend_fields: Set[str], frontend_fields: Set[str]) -> Dict:
    """检查字段兼容性"""
    issues = {
        "missing_in_backend": frontend_fields - backend_fields,
        "missing_in_frontend": backend_fields - frontend_fields,
        "potential_mappings": []
    }

    # 检查可能的字段映射问题
    for fe_field in issues["missing_in_backend"]:
        if fe_field in COMMON_FIELD_MAPPINGS:
            be_field = COMMON_FIELD_MAPPINGS[fe_field]
            if be_field in backend_fields:
                issues["potential_mappings"].append({
                    "frontend": fe_field,
                    "backend": be_field,
                    "suggestion": f"前端使用 {fe_field}，后端使用 {be_field}，需要字段映射"
                })

    return issues


def main():
    """主函数"""
    print("=" * 80)
    print("前后端字段匹配检查")
    print("=" * 80)
    print()

    # 检查目录是否存在
    if not BACKEND_API_DIR.exists():
        print(f"[ERROR] 后端 API 目录不存在: {BACKEND_API_DIR}")
        return

    if not FRONTEND_API_DIR.exists():
        print(f"[ERROR] 前端 API 目录不存在: {FRONTEND_API_DIR}")
        return

    # 扫描后端 API
    print("[INFO] 扫描后端 API...")
    backend_models = {}
    for py_file in BACKEND_API_DIR.glob("*.py"):
        if py_file.name.startswith("__"):
            continue
        models = extract_pydantic_fields(py_file)
        if models:
            backend_models[py_file.stem] = models
            print(f"  [OK] {py_file.name}: {len(models)} 个模型")

    print()

    # 扫描前端 API
    print("[INFO] 扫描前端 API...")
    frontend_interfaces = {}
    for ts_file in FRONTEND_API_DIR.glob("*.ts"):
        interfaces = extract_typescript_interfaces(ts_file)
        if interfaces:
            frontend_interfaces[ts_file.stem] = interfaces
            print(f"  [OK] {ts_file.name}: {len(interfaces)} 个接口")

    print()
    print("=" * 80)
    print("检查结果")
    print("=" * 80)
    print()

    # 匹配并检查
    issues_found = False

    for module_name in backend_models.keys():
        if module_name not in frontend_interfaces:
            continue

        be_models = backend_models[module_name]
        fe_interfaces = frontend_interfaces.get(module_name, {})

        # 尝试匹配模型和接口
        for be_model_name, be_fields in be_models.items():
            # 查找对应的前端接口
            fe_interface_name = None
            fe_fields = None

            # 尝试多种命名匹配
            possible_names = [
                be_model_name,
                be_model_name.replace("Create", ""),
                be_model_name.replace("Update", ""),
                be_model_name.replace("Response", ""),
            ]

            for name in possible_names:
                if name in fe_interfaces:
                    fe_interface_name = name
                    fe_fields = fe_interfaces[name]
                    break

            if not fe_fields:
                continue

            # 检查字段兼容性
            issues = check_field_compatibility(be_fields, fe_fields)

            if issues["missing_in_backend"] or issues["missing_in_frontend"] or issues["potential_mappings"]:
                issues_found = True
                print(f"[WARNING] {module_name}.py :: {be_model_name} <-> {fe_interface_name}")
                print()

                if issues["missing_in_backend"]:
                    print(f"  [MISSING_BE] 后端缺少字段: {', '.join(sorted(issues['missing_in_backend']))}")

                if issues["missing_in_frontend"]:
                    print(f"  [MISSING_FE] 前端缺少字段: {', '.join(sorted(issues['missing_in_frontend']))}")

                if issues["potential_mappings"]:
                    print(f"  [MAPPING] 可能的字段映射问题:")
                    for mapping in issues["potential_mappings"]:
                        print(f"     - {mapping['suggestion']}")

                print()

    if not issues_found:
        print("[OK] 未发现明显的字段不匹配问题")
    else:
        print()
        print("=" * 80)
        print("建议")
        print("=" * 80)
        print()
        print("1. 检查上述标记的字段不匹配问题")
        print("2. 在后端 API 中添加字段映射逻辑")
        print("3. 或者统一前后端的字段命名")
        print("4. 确保创建/更新接口正确处理字段转换")

    print()


if __name__ == "__main__":
    main()
