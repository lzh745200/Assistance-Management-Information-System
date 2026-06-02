#!/usr/bin/env python3
"""
测试新增组织后是否能看到
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def login():
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"].get("access_token")
        return data.get("access_token")
    else:
        print(f"登录失败: {response.status_code}")
        print(response.text)
        return None

def get_headers(token):
    """获取请求头"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_create_and_list():
    """测试创建组织后是否能在列表中看到"""
    print("=" * 60)
    print("测试新增组织后是否能看到")
    print("=" * 60)

    # 1. 登录
    print("\n1. 登录...")
    token = login()
    if not token:
        print("登录失败，测试终止")
        return
    print(f"登录成功")

    headers = get_headers(token)

    # 2. 查询当前组织数量
    print("\n2. 查询当前组织数量（is_active=true）...")
    response = requests.get(
        f"{BASE_URL}/organizations",
        headers=headers,
        params={"is_active": True, "page_size": 100}
    )

    if response.status_code == 200:
        data = response.json()
        before_count = data.get("total", 0)
        print(f"当前组织数量: {before_count}")
    else:
        print(f"查询失败: {response.status_code}")
        return

    # 3. 创建新组织
    print("\n3. 创建新组织...")
    import time
    timestamp = int(time.time())
    create_data = {
        "name": f"测试新增组织_{timestamp}",
        "code": f"TEST_NEW_{timestamp}",
        "org_type": "department",
        "is_active": True,
        "description": "测试新增后是否能看到"
    }

    response = requests.post(
        f"{BASE_URL}/organizations",
        headers=headers,
        json=create_data
    )

    if response.status_code != 200:
        print(f"创建组织失败: {response.status_code}")
        print(response.text)
        return

    org_data = response.json()
    org_id = org_data.get("id")
    org_is_active = org_data.get("is_active")
    print(f"创建成功！")
    print(f"  组织ID: {org_id}")
    print(f"  组织名称: {org_data.get('name')}")
    print(f"  is_active: {org_is_active}")

    # 4. 立即查询组织列表（is_active=true）
    print("\n4. 立即查询组织列表（is_active=true）...")
    response = requests.get(
        f"{BASE_URL}/organizations",
        headers=headers,
        params={"is_active": True, "page_size": 100}
    )

    if response.status_code == 200:
        data = response.json()
        after_count = data.get("total", 0)
        items = data.get("items", [])

        print(f"当前组织数量: {after_count}")
        print(f"数量变化: {before_count} -> {after_count} ({after_count - before_count:+d})")

        # 查找新创建的组织
        found = False
        for item in items:
            if item.get("id") == org_id:
                found = True
                print(f"\n[PASS] 找到新创建的组织:")
                print(f"  ID: {item.get('id')}")
                print(f"  名称: {item.get('name')}")
                print(f"  is_active: {item.get('is_active')}")
                break

        if not found:
            print(f"\n[FAIL] 未找到新创建的组织 (ID={org_id})")
            print("\n列表中的所有组织:")
            for item in items:
                print(f"  - ID: {item.get('id')}, 名称: {item.get('name')}, is_active: {item.get('is_active')}")
    else:
        print(f"查询失败: {response.status_code}")

    # 5. 查询所有组织（不传is_active）
    print("\n5. 查询所有组织（不传is_active）...")
    response = requests.get(
        f"{BASE_URL}/organizations",
        headers=headers,
        params={"page_size": 100}
    )

    if response.status_code == 200:
        data = response.json()
        all_count = data.get("total", 0)
        items = data.get("items", [])

        print(f"所有组织数量: {all_count}")

        # 查找新创建的组织
        found = False
        for item in items:
            if item.get("id") == org_id:
                found = True
                print(f"\n在所有组织列表中找到:")
                print(f"  ID: {item.get('id')}")
                print(f"  名称: {item.get('name')}")
                print(f"  is_active: {item.get('is_active')}")
                break

        if not found:
            print(f"\n在所有组织列表中也未找到 (ID={org_id})")
    else:
        print(f"查询失败: {response.status_code}")

    # 6. 直接查询组织详情
    print(f"\n6. 直接查询组织详情 (ID={org_id})...")
    response = requests.get(
        f"{BASE_URL}/organizations/{org_id}",
        headers=headers
    )

    if response.status_code == 200:
        org_detail = response.json()
        print(f"组织详情:")
        print(f"  ID: {org_detail.get('id')}")
        print(f"  名称: {org_detail.get('name')}")
        print(f"  is_active: {org_detail.get('is_active')}")
        print(f"  created_at: {org_detail.get('created_at')}")
    else:
        print(f"查询失败: {response.status_code}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_create_and_list()
