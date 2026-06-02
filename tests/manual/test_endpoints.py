import requests

# 登录
response = requests.post(
    "http://127.0.0.1:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["data"]["access_token"]

# 测试端点
endpoints = [
    "/health",
    "/system/health",
    "/dashboard",
    "/data/dashboard",
]

for endpoint in endpoints:
    url = f"http://127.0.0.1:8000/api/v1{endpoint}"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    print(f"{endpoint}: {response.status_code}")
