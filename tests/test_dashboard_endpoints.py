#!/usr/bin/env python3
import requests

# 登录
response = requests.post(
    "http://127.0.0.1:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 测试dashboard端点
endpoints = [
    "/dashboard/stats",
    "/dashboard/summary",
    "/dashboard/recent-activities",
]

print("测试dashboard端点:")
for endpoint in endpoints:
    url = f"http://127.0.0.1:8000/api/v1{endpoint}"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"  [OK] {endpoint}")
        else:
            print(f"  [FAIL] {endpoint}: 状态码 {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] {endpoint}: {str(e)[:50]}")
