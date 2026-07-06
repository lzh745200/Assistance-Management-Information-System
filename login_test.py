"""Quick login test."""
import requests
import json

r = requests.post(
    "http://127.0.0.1:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"},
    timeout=15
)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
