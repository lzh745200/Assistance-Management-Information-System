#!/usr/bin/env python3
"""
测试组织管理删除功能
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 测试用户登录
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
        # 响应格式: {"code": 200, "data": {"access_token": "..."}}
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

def test_organization_delete():
    """测试组织删除功能"""
    print("=" * 60)
    print("测试组织管理删除功能")
    print("=" * 60)

    # 1. 登录
    print("\n1. 登录...")
    token = login()
    if not token:
        print("登录失败，测试终止")
        return
    print(f"登录成功，token: {token[:20]}...")

    headers = get_headers(token)

    # 2. 创建测试组织
    print("\n2. 创建测试组织...")
    create_data = {
        "name": "测试组织_待删除",
        "code": "TEST_ORG_DELETE",
        "org_type": "department",
        "is_active": True,
        "description": "这是一个用于测试删除功能的组织"
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
    print(f"创建成功，组织ID: {org_id}")
    print(f"组织信息: {json.dumps(org_data, ensure_ascii=False, indent=2)}")

    # 3. 查询组织列表（删除前）
    print(f"\n3. 查询组织列表（删除前，is_active=true）...")
    response = requests.get(
        f"{BASE_URL}/organizations",
        headers=headers,
        params={"is_active": True, "page_size": 100}
    )

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        found = any(item.get("id") == org_id for item in items)
        print(f"总数: {data.get('total')}")
        print(f"测试组织在列表中: {'是' if found else '否'}")
    else:
        print(f"查询失败: {response.status_code}")

    # 4. 删除组织
    print(f"\n4. 删除组织 ID={org_id}...")
    response = requests.delete(
        f"{BASE_URL}/organizations/{org_id}",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"删除成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print(f"删除失败: {response.status_code}")
        print(response.text)
        return

    # 5. 查询组织列表（删除后，is_active=true）
    print(f"\n5. 查询组织列表（删除后，is_active=true）...")
    response = requests.get(
        f"{BASE_URL}/organizations",
        headers=headers,
        params={"is_active": True, "page_size": 100}
    )

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        found = any(item.get("id") == org_id for item in items)
        print(f"总数: {data.get('total')}")
        print(f"测试组织在列表中: {'是' if found else '否'}")

        if found:
            print("\n[FAIL] 测试失败：删除后组织仍然在列表中（is_active=true）")
        else:
            print("\n[PASS] 测试成功：删除后组织不在列表中（is_active=true）")
    else:
        print(f"查询失败: {response.status_code}")

    # 6. 查询组织列表（删除后，不传is_active）
    print(f"\n6. 查询组织列表（删除后，不传is_active）...")
    response = requests.get(
        f"{BASE_URL}/organizations",
        headers=headers,
        params={"page_size": 100}
    )

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        found_org = None
        for item in items:
            if item.get("id") == org_id:
                found_org = item
                break

        print(f"总数: {data.get('total')}")
        if found_org:
            print(f"测试组织在列表中: 是")
            print(f"is_active状态: {found_org.get('is_active')}")
            if found_org.get('is_active') == False:
                print("[PASS] 逻辑删除成功：is_active=False")
            else:
                print("[FAIL] 逻辑删除失败：is_active仍为True")
        else:
            print(f"测试组织在列表中: 否")
    else:
        print(f"查询失败: {response.status_code}")

    # 7. 直接查询组织详情
    print(f"\n7. 直接查询组织详情...")
    response = requests.get(
        f"{BASE_URL}/organizations/{org_id}",
        headers=headers
    )

    if response.status_code == 200:
        org_detail = response.json()
        print(f"组织详情: {json.dumps(org_detail, ensure_ascii=False, indent=2)}")
        print(f"is_active: {org_detail.get('is_active')}")
    else:
        print(f"查询失败: {response.status_code}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_organization_delete()
