"""测试乡村工作新增和列表显示"""
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 60)
print("测试乡村工作新增和列表显示")
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

# 2. 获取当前列表（不带年份筛选）
print("\n2. 获取当前列表（不带年份筛选）...")
list_resp = requests.get(
    f"{BASE_URL}/rural-works",
    headers=headers,
    params={"limit": 100}
)
if list_resp.status_code == 200:
    data = list_resp.json()
    before_count = data.get('total', 0)
    print(f"✓ 当前工作数量: {before_count}")
else:
    print(f"✗ 获取列表失败: {list_resp.status_code}")
    before_count = 0

# 3. 新增工作（不设置日期）
print("\n3. 新增工作（不设置日期）...")
create_resp = requests.post(
    f"{BASE_URL}/rural-works",
    headers=headers,
    json={
        "name": "测试工作-无日期",
        "type": "infrastructure",
        "status": "planned",
        "responsible_person": "测试人员",
        "progress": 0,
        "description": "测试新增工作是否显示在列表中"
    }
)
if create_resp.status_code == 200:
    work1 = create_resp.json()['data']
    print(f"✓ 新增成功，ID: {work1.get('id')}")
else:
    print(f"✗ 新增失败: {create_resp.status_code}")
    print(f"  响应: {create_resp.text}")
    work1 = None

# 4. 新增工作（设置当前年份日期）
print("\n4. 新增工作（设置当前年份日期）...")
current_year = datetime.now().year
create_resp2 = requests.post(
    f"{BASE_URL}/rural-works",
    headers=headers,
    json={
        "name": f"测试工作-{current_year}年",
        "type": "industry",
        "status": "in_progress",
        "responsible_person": "测试人员",
        "progress": 30,
        "start_date": f"{current_year}-01-01",
        "end_date": f"{current_year}-12-31",
        "description": "测试带日期的工作"
    }
)
if create_resp2.status_code == 200:
    work2 = create_resp2.json()['data']
    print(f"✓ 新增成功，ID: {work2.get('id')}")
else:
    print(f"✗ 新增失败: {create_resp2.status_code}")
    work2 = None

# 5. 获取列表（不带年份筛选）
print("\n5. 获取列表（不带年份筛选）...")
list_resp = requests.get(
    f"{BASE_URL}/rural-works",
    headers=headers,
    params={"limit": 100}
)
if list_resp.status_code == 200:
    data = list_resp.json()
    after_count = data.get('total', 0)
    print(f"✓ 当前工作数量: {after_count}")
    print(f"  新增数量: {after_count - before_count}")

    # 检查新增的工作是否在列表中
    items = data.get('items', [])
    if work1:
        found1 = any(item['id'] == work1['id'] for item in items)
        print(f"  无日期工作: {'✓ 已显示' if found1 else '✗ 未显示'}")
    if work2:
        found2 = any(item['id'] == work2['id'] for item in items)
        print(f"  有日期工作: {'✓ 已显示' if found2 else '✗ 未显示'}")
else:
    print(f"✗ 获取列表失败: {list_resp.status_code}")

# 6. 获取列表（带当前年份筛选）
print(f"\n6. 获取列表（筛选 {current_year} 年）...")
list_resp = requests.get(
    f"{BASE_URL}/rural-works",
    headers=headers,
    params={"limit": 100, "year": current_year}
)
if list_resp.status_code == 200:
    data = list_resp.json()
    year_count = data.get('total', 0)
    print(f"✓ {current_year}年工作数量: {year_count}")

    items = data.get('items', [])
    if work1:
        found1 = any(item['id'] == work1['id'] for item in items)
        print(f"  无日期工作: {'✗ 未显示（正确）' if not found1 else '✓ 已显示（错误）'}")
    if work2:
        found2 = any(item['id'] == work2['id'] for item in items)
        print(f"  有日期工作: {'✓ 已显示' if found2 else '✗ 未显示'}")
else:
    print(f"✗ 获取列表失败: {list_resp.status_code}")

# 7. 清理测试数据
print("\n7. 清理测试数据...")
if work1:
    del_resp = requests.delete(f"{BASE_URL}/rural-works/{work1['id']}", headers=headers)
    print(f"  删除工作1: {'✓' if del_resp.status_code == 200 else '✗'}")
if work2:
    del_resp = requests.delete(f"{BASE_URL}/rural-works/{work2['id']}", headers=headers)
    print(f"  删除工作2: {'✓' if del_resp.status_code == 200 else '✗'}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
