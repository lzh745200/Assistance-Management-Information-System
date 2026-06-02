"""测试数据包导出验证"""
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. 登录获取 token
print("1. 登录获取 token...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"登录失败: {login_response.status_code}")
    print(login_response.text)
    exit(1)

login_data = login_response.json()
token = login_data.get("access_token") or login_data.get("data", {}).get("access_token")
if not token:
    print(f"无法获取 token: {json.dumps(login_data, ensure_ascii=False)}")
    exit(1)

print(f"✓ 登录成功，token: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}"}

# 2. 测试空 data_types（应该返回 422 验证错误）
print("\n2. 测试空 data_types...")
export_response = requests.post(
    f"{BASE_URL}/data-packages/export",
    headers=headers,
    json={"data_types": [], "description": "test", "type": "report"}
)

print(f"状态码: {export_response.status_code}")
print(f"响应: {json.dumps(export_response.json(), ensure_ascii=False, indent=2)}")

if export_response.status_code == 422:
    print("✓ 验证成功：空 data_types 被正确拒绝")
    error_detail = export_response.json().get("detail", [])
    if isinstance(error_detail, list) and len(error_detail) > 0:
        print(f"  错误信息: {error_detail[0].get('msg', '')}")
elif export_response.status_code == 400:
    print("✓ 验证成功：空 data_types 被正确拒绝（400 错误）")
    print(f"  错误信息: {export_response.json().get('detail', '')}")
else:
    print(f"✗ 验证失败：期望 422 或 400，实际 {export_response.status_code}")

# 3. 测试有效的 data_types
print("\n3. 测试有效的 data_types...")
export_response = requests.post(
    f"{BASE_URL}/data-packages/export",
    headers=headers,
    json={"data_types": ["villages"], "description": "test", "type": "report"}
)

print(f"状态码: {export_response.status_code}")
if export_response.status_code in [200, 201]:
    print("✓ 导出成功")
    result = export_response.json()
    print(f"  package_id: {result.get('package_id')}")
else:
    print(f"✗ 导出失败: {export_response.status_code}")
    print(f"  响应: {json.dumps(export_response.json(), ensure_ascii=False, indent=2)}")
