"""API smoke test - login and test all critical endpoints."""
import requests

s = requests.Session()
base = "http://127.0.0.1:8000"

# Login
r = s.post(f"{base}/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
print(f"Login: {r.status_code} - {r.json().get('message', '')}")

token = r.json().get("data", {}).get("access_token", "")
if not token:
    print("ERROR: No token received!")
    exit(1)

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
    "/api/v1/system/health",
]

all_ok = True
for ep in endpoints:
    try:
        r = s.get(f"{base}{ep}", headers=h, timeout=10)
        status = r.status_code
        if status == 200:
            print(f"  OK  {ep}: {status}")
        else:
            print(f"  FAIL {ep}: {status} - {r.text[:100]}")
            all_ok = False
    except Exception as e:
        print(f"  ERR  {ep}: {e}")
        all_ok = False

if all_ok:
    print("\n✅ All endpoints OK!")
else:
    print("\n❌ Some endpoints failed!")
