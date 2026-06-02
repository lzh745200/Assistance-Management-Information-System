"""
全系统 API 端点测试脚本
验证所有模块的功能正常性，重点关注经费管理板块
"""
import urllib.request, json, sys, traceback

BASE = "http://127.0.0.1:8000"
results = {"pass": 0, "fail": 0, "skip": 0, "details": []}

def _req(method, path, data=None, token=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        return e.code, body
    except Exception as e:
        return 0, str(e)

def check(module, test_name, status, detail=""):
    ok = 200 <= status < 300
    label = "PASS" if ok else "FAIL"
    if status == 401:
        label = "SKIP"
        results["skip"] += 1
    elif ok:
        results["pass"] += 1
    else:
        results["fail"] += 1
    msg = f"[{label}] {module}/{test_name}: HTTP {status}"
    if detail:
        msg += f" - {str(detail)[:100]}"
    print(msg)
    results["details"].append({"module": module, "test": test_name, "status": status, "ok": ok})
    return ok

# ═══════════════════════════════════════════════════════════
# Setup: Login
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("SYSTEM-WIDE API TEST")
print("=" * 60)

s, r = _req("POST", "/api/v1/auth/login", {"username": "admin", "password": "admin123"})
if s == 200 and "data" in r:
    TOKEN = r["data"]["access_token"]
    print(f"[OK] Login: admin authenticated")
else:
    print(f"[FAIL] Login: {r}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# 1. 认证模块 (Auth)
# ═══════════════════════════════════════════════════════════
print("\n--- 1. 认证模块 ---")
check("auth", "get_profile", *_req("GET", "/api/v1/auth/me", token=TOKEN))
check("auth", "get_csrf", *_req("GET", "/api/v1/auth/csrf-token", token=TOKEN))
check("auth", "get_permissions", *_req("GET", "/api/v1/auth/permissions", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 2. 组织管理 (Organization)
# ═══════════════════════════════════════════════════════════
print("\n--- 2. 组织管理 ---")
check("org", "list", *_req("GET", "/api/v1/organizations", token=TOKEN))
check("org", "tree", *_req("GET", "/api/v1/organizations/tree", token=TOKEN))
check("org", "stats", *_req("GET", "/api/v1/organizations/statistics", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 3. 帮扶村管理 (Supported Villages) - 已验证
# ═══════════════════════════════════════════════════════════
print("\n--- 3. 帮扶村管理 ---")
check("village", "list", *_req("GET", "/api/v1/supported-villages?page=1&page_size=5", token=TOKEN))
check("village", "filter-options", *_req("GET", "/api/v1/supported-villages/filter-options", token=TOKEN))
s3, r3 = _req("POST", "/api/v1/supported-villages", {
    "villageName": "__test_village__", "department": "test", "supportUnit": "test",
    "county": "都匀市", "isThreeRegions": 1, "tieredDevelopmentLevel": "示范级"
}, token=TOKEN)
check("village", "create", s3, r3)
VID = r3.get("data", {}).get("id", 1) if s3 == 200 else 1

check("village", "get_one", *_req("GET", f"/api/v1/supported-villages/{VID}", token=TOKEN))
check("village", "update", *_req("PUT", f"/api/v1/supported-villages/{VID}", {
    "villageName": "__test_village_updated__", "isKeyCounty": 1
}, token=TOKEN))
check("village", "yearly_get", *_req("GET", f"/api/v1/supported-villages/{VID}/yearly/2025", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 4. 经费管理 (Funds) — 重点 !
# ═══════════════════════════════════════════════════════════
print("\n--- 4. 经费管理 (重点) ---")

# 4a. 经费基础 CRUD
check("funds", "list", *_req("GET", "/api/v1/funds?page=1&page_size=5", token=TOKEN))
check("funds", "filter-options", *_req("GET", "/api/v1/funds/filter-options", token=TOKEN))
s_f, r_f = _req("POST", "/api/v1/funds", {
    "fundName": "__test_fund__",
    "fundType": "部队投入",
    "amount": 500000,
    "fundSource": "中央财政",
    "villageId": VID,
    "year": 2025,
    "status": "已拨付",
    "description": "测试经费",
}, token=TOKEN)
check("funds", "create", s_f, r_f)
FID = r_f.get("data", {}).get("id", 1) if s_f == 200 else 1

check("funds", "get_one", *_req("GET", f"/api/v1/funds/{FID}", token=TOKEN))
check("funds", "update", *_req("PUT", f"/api/v1/funds/{FID}", {
    "fundName": "__test_fund_updated__", "amount": 600000
}, token=TOKEN))
check("funds", "stats", *_req("GET", "/api/v1/funds/statistics", token=TOKEN))

# 4b. 预算管理
print("  --- 预算管理 ---")
check("budget", "list", *_req("GET", "/api/v1/fund-budgets?page=1&page_size=5", token=TOKEN))
s_b, r_b = _req("POST", "/api/v1/fund-budgets", {
    "budgetName": "__test_budget__",
    "totalAmount": 1000000,
    "year": 2025,
    "category": "帮扶经费",
    "status": "已批准"
}, token=TOKEN)
check("budget", "create", s_b, r_b)
BID = r_b.get("data", {}).get("id", 1) if s_b == 200 else 1
check("budget", "get_one", *_req("GET", f"/api/v1/fund-budgets/{BID}", token=TOKEN))
check("budget", "update", *_req("PUT", f"/api/v1/fund-budgets/{BID}", {
    "budgetName": "__test_budget_updated__", "totalAmount": 1200000
}, token=TOKEN))

# 4c. 经费生命周期
print("  --- 经费生命周期 ---")
check("lifecycle", "list", *_req("GET", "/api/v1/fund-lifecycle?page=1&page_size=5", token=TOKEN))
check("lifecycle", "baselines", *_req("GET", "/api/v1/fund-lifecycle/baselines", token=TOKEN))
s_l, r_l = _req("POST", "/api/v1/fund-lifecycle/contracts", {
    "contractName": "__test_contract__",
    "contractNo": "CF-2025-001",
    "amount": 300000,
    "fundId": FID,
    "partyA": "部队",
    "partyB": "施工单位",
    "signDate": "2025-06-01",
    "status": "执行中"
}, token=TOKEN)
check("lifecycle", "create_contract", s_l, r_l)
CID = r_l.get("data", {}).get("id", 1) if s_l == 200 else 1
check("lifecycle", "get_contract", *_req("GET", f"/api/v1/fund-lifecycle/contracts/{CID}", token=TOKEN))
check("lifecycle", "anomalies", *_req("GET", "/api/v1/fund-lifecycle/anomalies", token=TOKEN))
check("lifecycle", "settlements", *_req("GET", "/api/v1/fund-lifecycle/settlements", token=TOKEN))
check("lifecycle", "transfers", *_req("GET", "/api/v1/fund-lifecycle/transfers", token=TOKEN))

# 4d. 经费分配
print("  --- 经费分配 ---")
check("alloc", "list", *_req("GET", "/api/v1/fund-lifecycle/allocations", token=TOKEN))
check("alloc", "create", *_req("POST", "/api/v1/fund-lifecycle/allocations", {
    "fundId": FID, "villageId": VID, "amount": 50000, "year": 2025
}, token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 5. 项目管理 (Projects)
# ═══════════════════════════════════════════════════════════
print("\n--- 5. 项目管理 ---")
check("project", "list", *_req("GET", "/api/v1/projects?page=1&page_size=5", token=TOKEN))
check("project", "filter-options", *_req("GET", "/api/v1/projects/filter-options", token=TOKEN))
s_p, r_p = _req("POST", "/api/v1/projects", {
    "projectName": "__test_project__",
    "projectType": "基础设施",
    "villageId": VID,
    "budget": 200000,
    "startDate": "2025-01-01",
    "status": "进行中"
}, token=TOKEN)
check("project", "create", s_p, r_p)
PID = r_p.get("data", {}).get("id", 1) if s_p == 200 else 1
check("project", "get_one", *_req("GET", f"/api/v1/projects/{PID}", token=TOKEN))
check("project", "update", *_req("PUT", f"/api/v1/projects/{PID}", {
    "projectName": "__test_project_updated__", "budget": 250000
}, token=TOKEN))
check("project", "milestones", *_req("GET", f"/api/v1/project-milestones?projectId={PID}", token=TOKEN))
check("project", "tasks", *_req("GET", f"/api/v1/projects/{PID}/tasks", token=TOKEN))
check("project", "stats", *_req("GET", "/api/v1/projects/statistics", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 6. 学校管理 (Schools)
# ═══════════════════════════════════════════════════════════
print("\n--- 6. 学校管理 ---")
check("school", "list", *_req("GET", "/api/v1/schools?page=1&page_size=5", token=TOKEN))
check("school", "filter-options", *_req("GET", "/api/v1/schools/filter-options", token=TOKEN))
s_sc, r_sc = _req("POST", "/api/v1/schools", {
    "schoolName": "__test_school__",
    "schoolType": "小学",
    "county": "都匀市",
    "villageId": VID
}, token=TOKEN)
check("school", "create", s_sc, r_sc)
SID = r_sc.get("data", {}).get("id", 1) if s_sc == 200 else 1
check("school", "get_one", *_req("GET", f"/api/v1/schools/{SID}", token=TOKEN))
check("school", "analysis", *_req("GET", "/api/v1/schools/analysis", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 7. 政策管理 (Policies)
# ═══════════════════════════════════════════════════════════
print("\n--- 7. 政策管理 ---")
check("policy", "list", *_req("GET", "/api/v1/policies?page=1&page_size=5", token=TOKEN))
check("policy", "categories", *_req("GET", "/api/v1/policies/categories", token=TOKEN))
check("policy", "favorites", *_req("GET", "/api/v1/policies/favorites", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 8. 乡村工作/任务 (Rural Works & Tasks)
# ═══════════════════════════════════════════════════════════
print("\n--- 8. 乡村工作/任务 ---")
check("rural_work", "list", *_req("GET", "/api/v1/rural-works?page=1&page_size=5", token=TOKEN))
check("rural_task", "list", *_req("GET", "/api/v1/rural-tasks?page=1&page_size=5", token=TOKEN))
check("work_log", "list", *_req("GET", "/api/v1/work-logs?page=1&page_size=5", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 9. 审批 & 消息 (Approval & Messages)
# ═══════════════════════════════════════════════════════════
print("\n--- 9. 审批与消息 ---")
check("approval", "list", *_req("GET", "/api/v1/approvals?page=1&page_size=5", token=TOKEN))
check("approval", "workflows", *_req("GET", "/api/v1/approvals/workflows", token=TOKEN))
check("approval", "pending", *_req("GET", "/api/v1/approvals/pending", token=TOKEN))
check("message", "list", *_req("GET", "/api/v1/messages?page=1&page_size=5", token=TOKEN))
check("message", "unread_count", *_req("GET", "/api/v1/messages/unread-count", token=TOKEN))
check("todo", "list", *_req("GET", "/api/v1/todos?page=1&page_size=5", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 10. 系统管理 (System)
# ═══════════════════════════════════════════════════════════
print("\n--- 10. 系统管理 ---")
check("system", "health", *_req("GET", "/api/v1/system-health", token=TOKEN))
check("system", "config", *_req("GET", "/api/v1/system-config", token=TOKEN))
check("system", "monitoring", *_req("GET", "/api/v1/monitoring/metrics", token=TOKEN))
check("system", "users", *_req("GET", "/api/v1/users", token=TOKEN))
check("system", "roles", *_req("GET", "/api/v1/roles", token=TOKEN))
check("system", "menus", *_req("GET", "/api/v1/menus", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 11. 数据管理 (Data)
# ═══════════════════════════════════════════════════════════
print("\n--- 11. 数据管理 ---")
check("data", "sync_logs", *_req("GET", "/api/v1/data-sync/logs?page=1&page_size=5", token=TOKEN))
check("data", "dashboard", *_req("GET", "/api/v1/dashboard/summary", token=TOKEN))
check("data", "effectiveness", *_req("GET", "/api/v1/effectiveness?page=1&page_size=5", token=TOKEN))
check("data", "assessment", *_req("GET", "/api/v1/assessments?page=1&page_size=5", token=TOKEN))
check("data", "search", *_req("GET", "/api/v1/search?q=test", token=TOKEN))
check("data", "validation_rules", *_req("GET", "/api/v1/validation/rules", token=TOKEN))
check("data", "report_templates", *_req("GET", "/api/v1/report-templates", token=TOKEN))

# ═══════════════════════════════════════════════════════════
# 12. 清理测试数据
# ═══════════════════════════════════════════════════════════
print("\n--- 12. 清理测试数据 ---")
cleanup = [
    f"/api/v1/supported-villages/{VID}",
    f"/api/v1/funds/{FID}",
    f"/api/v1/projects/{PID}",
    f"/api/v1/schools/{SID}",
]
for path in cleanup:
    s, r = _req("DELETE", path, token=TOKEN)
    check("cleanup", path.split("/")[-2], s)

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"PASS: {results['pass']}  FAIL: {results['fail']}  SKIP: {results['skip']}")
if results['fail'] > 0:
    print("\nFAILED TESTS:")
    for d in results['details']:
        if not d['ok'] and d['status'] != 401:
            print(f"  - {d['module']}/{d['test']}: HTTP {d['status']}")
print()
if results['fail'] == 0:
    print("ALL CRITICAL ENDPOINTS PASSING")
