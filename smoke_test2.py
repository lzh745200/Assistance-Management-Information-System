"""API smoke test - test endpoints that don't require auth."""
import requests

base = "http://127.0.0.1:8000"

# Test no-auth endpoints
tests = [
    ("CSRF", "GET", "/api/v1/auth/csrf-token"),
    ("Docs", "GET", "/docs"),
    ("OpenAPI", "GET", "/openapi.json"),
]

for name, method, path in tests:
    try:
        r = requests.request(method, f"{base}{path}", timeout=5)
        print(f"  {name}: {r.status_code}")
    except Exception as e:
        print(f"  {name}: ERR - {e}")

# Try login with default credentials
for user, pwd in [("admin", "admin123"), ("admin", "Admin@123"), ("admin", "admin")]:
    r = requests.post(f"{base}/api/v1/auth/login", json={"username": user, "password": pwd}, timeout=5)
    print(f"  Login({user}/{pwd}): {r.status_code} - {r.json().get('message', '')}")
    if r.status_code == 200:
        token = r.json().get("data", {}).get("access_token", "")
        h = {"Authorization": f"Bearer {token}"}
        # Test critical endpoints
        for ep in ["/api/v1/supported-villages", "/api/v1/funds", "/api/v1/projects", "/api/v1/schools", "/api/v1/work-logs"]:
            r2 = requests.get(f"{base}{ep}", headers=h, timeout=10)
            print(f"    {ep}: {r2.status_code}")
        break
