#!/usr/bin/env python3
"""
测试端点路径
"""
import requests

def test_endpoints():
    # 登录
    print("登录...")
    response = requests.post(
        "http://127.0.0.1:8000/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = response.json()["data"]["access_token"]
    print(f"登录成功")

    headers = {"Authorization": f"Bearer {token}"}

    # 测试端点
    endpoints = [
        "/health",
        "/system/health",
        "/dashboard",
        "/data/dashboard",
    ]

    print("\n测试端点:")
    for endpoint in endpoints:
        url = f"http://127.0.0.1:8000/api/v1{endpoint}"
        try:
            response = requests.get(url, headers=headers, timeout=5)
            status = "OK" if response.status_code == 200 else f"状态码: {response.status_code}"
            print(f"  {endpoint}: {status}")
        except Exception as e:
            print(f"  {endpoint}: 错误 - {str(e)[:50]}")

if __name__ == "__main__":
    test_endpoints()
