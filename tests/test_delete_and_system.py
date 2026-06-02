"""测试系统接口和删除功能"""
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 60)
print("测试系统接口和删除功能")
print("=" * 60)

# 1. 登录
print("\n1. 登录...")
login_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "admin123"}
)
if login_resp.status_code == 200:
    token = login_resp.json()['data']['access_token']
    print("✓ 登录成功")
else:
    print(f"✗ 登录失败: {login_resp.status_code}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 2. 测试 /system/config 接口
print("\n2. 测试 /system/config 接口...")
config_resp = requests.get(f"{BASE_URL}/system/config", headers=headers)
print(f"状态码: {config_resp.status_code}")
if config_resp.status_code == 200:
    print("✓ 接口正常")
    data = config_resp.json()
    print(f"  配置项数量: {len(data) if isinstance(data, dict) else 'N/A'}")
elif config_resp.status_code == 404:
    print("✗ 404 错误 - 接口未找到")
else:
    print(f"⚠ 其他错误: {config_resp.text[:100]}")

# 3. 测试 /system/update-logs 接口
print("\n3. 测试 /system/update-logs 接口...")
logs_resp = requests.get(f"{BASE_URL}/system/update-logs", headers=headers)
print(f"状态码: {logs_resp.status_code}")
if logs_resp.status_code == 200:
    print("✓ 接口正常")
    data = logs_resp.json()
    if isinstance(data, dict):
        print(f"  日志数量: {data.get('total', 0)}")
    elif isinstance(data, list):
        print(f"  日志数量: {len(data)}")
elif logs_resp.status_code == 404:
    print("✗ 404 错误 - 接口未找到")
else:
    print(f"⚠ 其他错误: {logs_resp.text[:100]}")

# 4. 测试删除功能（创建并删除一个测试工作）
print("\n4. 测试删除功能...")

# 4.1 创建测试工作
print("  4.1 创建测试工作...")
create_resp = requests.post(
    f"{BASE_URL}/rural-works",
    headers=headers,
    json={
        "name": "测试删除功能",
        "type": "infrastructure",
        "status": "planned",
        "responsible_person": "测试",
        "progress": 0,
        "description": "用于测试删除功能"
    }
)
if create_resp.status_code == 200:
    work_id = create_resp.json()['data']['id']
    print(f"  ✓ 创建成功，ID: {work_id}")

    # 4.2 删除测试工作
    print("  4.2 删除测试工作...")
    delete_resp = requests.delete(
        f"{BASE_URL}/rural-works/{work_id}",
        headers=headers
    )
    print(f"  状态码: {delete_resp.status_code}")
    if delete_resp.status_code == 200:
        print("  ✓ 删除成功")
    else:
        print(f"  ✗ 删除失败: {delete_resp.text[:100]}")

    # 4.3 验证删除
    print("  4.3 验证删除...")
    get_resp = requests.get(
        f"{BASE_URL}/rural-works/{work_id}",
        headers=headers
    )
    if get_resp.status_code == 404:
        print("  ✓ 记录已删除（404）")
    elif get_resp.status_code == 200:
        print("  ✗ 记录仍然存在")
    else:
        print(f"  ⚠ 状态码: {get_resp.status_code}")
else:
    print(f"  ✗ 创建失败: {create_resp.status_code}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
