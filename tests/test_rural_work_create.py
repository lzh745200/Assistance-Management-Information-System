#!/usr/bin/env python3
"""
测试乡村工作新增功能
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 登录
print("1. 登录...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("登录成功")

# 查询当前工作数量
print("\n2. 查询当前工作数量...")
response = requests.get(
    f"{BASE_URL}/rural-works",
    headers=headers,
    params={"skip": 0, "limit": 100}
)
data = response.json()
before_count = data.get("total", 0)
print(f"当前工作数量: {before_count}")
print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")

# 创建新工作
print("\n3. 创建新工作...")
import time
timestamp = int(time.time())
create_data = {
    "name": f"测试工作_{timestamp}",
    "type": "infrastructure",
    "status": "planned",
    "description": "测试新增功能",
    "responsible_person": "测试人员",
    "progress": 0
}

response = requests.post(
    f"{BASE_URL}/rural-works",
    headers=headers,
    json=create_data
)

if response.status_code == 200:
    result = response.json()
    print(f"创建成功！")
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

    if "data" in result:
        work_id = result["data"].get("id")
        print(f"工作ID: {work_id}")
else:
    print(f"创建失败: {response.status_code}")
    print(response.text)
    exit(1)

# 立即查询工作列表
print("\n4. 立即查询工作列表...")
response = requests.get(
    f"{BASE_URL}/rural-works",
    headers=headers,
    params={"skip": 0, "limit": 100}
)
data = response.json()
after_count = data.get("total", 0)
items = data.get("items", [])

print(f"当前工作数量: {after_count}")
print(f"数量变化: {before_count} -> {after_count} ({after_count - before_count:+d})")

# 查找新创建的工作
found = False
for item in items:
    if item.get("name") == create_data["name"]:
        found = True
        print(f"\n[PASS] 找到新创建的工作:")
        print(f"  ID: {item.get('id')}")
        print(f"  名称: {item.get('name')}")
        print(f"  类型: {item.get('type')}")
        print(f"  状态: {item.get('status')}")
        break

if not found:
    print(f"\n[FAIL] 未找到新创建的工作")
    print(f"\n列表中的所有工作:")
    for item in items[:5]:  # 只显示前5个
        print(f"  - ID: {item.get('id')}, 名称: {item.get('name')}")
