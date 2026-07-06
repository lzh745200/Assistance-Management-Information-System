"""API smoke test - login and test all critical endpoints."""
import requests

base = "http://127.0.0.1:8000"

# Login with reset password
r = requests.post(f"{base}/api/v1/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
print(f"Login: {r.status_code} - {r.json().get('message', '')}")

if r.status_code != 200:
    print("Login failed!")
    exit(1)

token = r.json().get("data", {}).get("access_token", "")
h = {"Authorization": f"Bearer {token}"}

# Test critical endpoints
endpoints = [
    "/api/v1/supported-villages",
    "/api/v1/funds",
    "/api/v1/projects",
    "/api/v1/schools",
    "/api/v1/work-logs",
    "/api/v1/organizations",
    "/api/v1/policies",
    "/api/v1/dashboard/stats",
]

all_ok = True
for ep in endpoints:
    try:
        r = requests.get(f"{base}{ep}", headers=h, timeout=10)
        if r.status_code == 200:
            print(f"  OK  {ep}: {r.status_code}")
        else:
            print(f"  FAIL {ep}: {r.status_code} - {r.text[:150]}")
            all_ok = False
    except Exception as e:
        print(f"  ERR  {ep}: {e}")
        all_ok = False

print("\n✅ All endpoints OK!" if all_ok else "\n❌ Some endpoints failed!")
