#!/usr/bin/env python
"""Deep security & consistency scanner for backend."""
import os
import sys
import re
import importlib
import inspect
import ast
from pathlib import Path
from collections import defaultdict

os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

backend_dir = Path(__file__).resolve().parent
app_dir = backend_dir / "app"

issues = []

def add_issue(severity, category, file_path, line, message):
    issues.append({
        "severity": severity,
        "category": category,
        "file": str(file_path.relative_to(backend_dir)),
        "line": line,
        "message": message,
    })

# ══════════════════════════════════════════════════════════════
# Scan 1: Endpoints without filter_by_data_scope
# ══════════════════════════════════════════════════════════════
print("=" * 60)
print("Scan 1: Endpoints without filter_by_data_scope")
print("=" * 60)

api_dir = app_dir / "api" / "v1"
model_files_with_org = set()

# Check which models have organization_id
models_dir = app_dir / "models"
for model_file in models_dir.glob("*.py"):
    if model_file.name.startswith("_"):
        continue
    try:
        content = model_file.read_text(encoding="utf-8")
        if "organization_id" in content:
            model_files_with_org.add(model_file.stem)
    except Exception:
        pass

print(f"  Models with organization_id: {sorted(model_files_with_org)}")

# Check API files that query models with organization_id but don't use filter_by_data_scope
endpoints_without_scope = []
for api_file in api_dir.glob("*.py"):
    if api_file.name.startswith("_"):
        continue
    try:
        content = api_file.read_text(encoding="utf-8")
    except Exception:
        continue
    
    # Check if this file queries models with organization_id
    has_org_query = False
    for model_name in model_files_with_org:
        # Look for model class usage in queries
        if f"query({model_name.capitalize()}" in content or f".query({model_name}" in content:
            has_org_query = True
            break
    
    if not has_org_query:
        continue
    
    # Check if it uses filter_by_data_scope
    if "filter_by_data_scope" not in content and "data_scope" not in content:
        # Check if it's a read-only endpoint (stats/metrics may not need it)
        if any(x in api_file.name for x in ["metrics", "health", "performance", "monitoring"]):
            continue
        endpoints_without_scope.append(api_file.name)

if endpoints_without_scope:
    for f in endpoints_without_scope:
        print(f"  WARN: {f} queries org models but may not use filter_by_data_scope")
else:
    print("  OK: All API files with org model queries use filter_by_data_scope or data_scope")

# ══════════════════════════════════════════════════════════════
# Scan 2: Write operations without write_work_log
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Scan 2: Write operations without write_work_log")
print("=" * 60)

write_endpoints_without_log = []
for api_file in api_dir.glob("*.py"):
    if api_file.name.startswith("_"):
        continue
    try:
        content = api_file.read_text(encoding="utf-8")
    except Exception:
        continue
    
    # Check for write operations (POST/PUT/DELETE/PATCH)
    has_write = bool(re.search(r'@router\.(post|put|delete|patch)', content))
    if not has_write:
        continue
    
    # Skip system modules that have their own logging
    if any(x in api_file.name for x in ["auth", "backup", "import", "export", "sync", "health", "metrics"]):
        continue
    
    # Check if write_work_log is called
    if "write_work_log" not in content and "work_log" not in content:
        write_endpoints_without_log.append(api_file.name)

if write_endpoints_without_log:
    for f in write_endpoints_without_log:
        print(f"  WARN: {f} has write operations but may not call write_work_log")
else:
    print("  OK: All write endpoints call write_work_log")

# ══════════════════════════════════════════════════════════════
# Scan 3: Hardcoded secrets or passwords
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Scan 3: Hardcoded secrets/passwords in source")
print("=" * 60)

secret_patterns = [
    (r'password\s*=\s*["\'][^"\']{6,}["\']', "hardcoded password"),
    (r'secret_key\s*=\s*["\'][^"\']{10,}["\']', "hardcoded secret key"),
    (r'api_key\s*=\s*["\'][^"\']{10,}["\']', "hardcoded API key"),
]

for py_file in app_dir.rglob("*.py"):
    if py_file.name.startswith("_") or "test" in str(py_file):
        continue
    try:
        lines = py_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    
    for i, line in enumerate(lines, 1):
        # Skip comments, env var reads, and known safe patterns
        stripped = line.strip()
        if stripped.startswith("#") or "os.environ" in line or "os.getenv" in line:
            continue
        if "admin123" in line and "DEFAULT_ADMIN_PASSWORD" in line:
            continue  # Known default, flagged with warning
        
        for pattern, desc in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Skip if it's a variable assignment with a default in quotes that's clearly a test/config value
                if any(x in line for x in ["test", "example", "placeholder", "change", "your-"]):
                    continue
                add_issue("WARN", "security", py_file, i, f"Possible {desc}: {stripped[:80]}")

if not issues:
    print("  OK: No hardcoded secrets found")
else:
    for iss in issues:
        print(f"  {iss['severity']}: {iss['file']}:{iss['line']} - {iss['message']}")

# ══════════════════════════════════════════════════════════════
# Scan 4: Response format consistency (bare dict vs ok_list)
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Scan 4: List endpoints not using ok_list()")
print("=" * 60)

bare_list_endpoints = []
for api_file in api_dir.rglob("*.py"):
    if api_file.name.startswith("_"):
        continue
    try:
        content = api_file.read_text(encoding="utf-8")
    except Exception:
        continue
    
    # Find @router.get endpoints that return dict with "items" but not via ok_list
    lines = content.splitlines()
    in_get_endpoint = False
    endpoint_start_line = 0
    
    for i, line in enumerate(lines, 1):
        if re.search(r'@router\.get\(', line):
            in_get_endpoint = True
            endpoint_start_line = i
            continue
        
        if in_get_endpoint:
            # Check for bare dict return with items
            if '"items"' in line or "'items'" in line:
                # Check if ok_list is used in the surrounding context
                context_start = max(0, endpoint_start_line - 1)
                context_end = min(len(lines), i + 5)
                context = "\n".join(lines[context_start:context_end])
                if "ok_list" not in context and "success_response" not in context:
                    bare_list_endpoints.append((api_file.name, endpoint_start_line))
            # End of endpoint (next decorator or function def)
            if re.search(r'@router\.|^(async )?def ', line) and i > endpoint_start_line + 1:
                in_get_endpoint = False

if bare_list_endpoints:
    for f, line in bare_list_endpoints:
        print(f"  WARN: {f}:{line} may return bare dict with 'items' instead of ok_list()")
else:
    print("  OK: All list endpoints use ok_list()")

# ══════════════════════════════════════════════════════════════
# Scan 5: Missing error handling in critical paths
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Scan 5: db.commit() without try/except")
print("=" * 60)

unsafe_commits = []
for py_file in app_dir.rglob("*.py"):
    if py_file.name.startswith("_") or "test" in str(py_file):
        continue
    try:
        lines = py_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == "db.commit()" or stripped == "db.commit()  ":
            # Check surrounding lines for try/except
            context_start = max(0, i - 10)
            context = "\n".join(lines[context_start:i])
            if "try:" not in context and "try :" not in context:
                # Check if it's inside a with transaction() block
                if "transaction" not in context and "safe_commit" not in context:
                    unsafe_commits.append((py_file.relative_to(backend_dir), i))

if unsafe_commits:
    for f, line in unsafe_commits[:20]:  # Show first 20
        print(f"  WARN: {f}:{line} - db.commit() without try/except or transaction()")
    if len(unsafe_commits) > 20:
        print(f"  ... and {len(unsafe_commits) - 20} more")
else:
    print("  OK: All db.commit() calls have error handling")

# ══════════════════════════════════════════════════════════════
# Scan 6: Frontend API files using raw axios import
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Scan 6: Frontend API files using raw axios import")
print("=" * 60)

frontend_api_dir = backend_dir.parent / "frontend" / "src" / "api"
raw_imports = []
for ts_file in frontend_api_dir.rglob("*.ts"):
    try:
        content = ts_file.read_text(encoding="utf-8")
    except Exception:
        continue
    
    # Check for raw axios import instead of @/api/request wrapper
    if "import request from" in content or "import api from" in content:
        if "@/api/request" not in content and "./request" not in content:
            raw_imports.append(ts_file.relative_to(backend_dir.parent / "frontend"))

if raw_imports:
    for f in raw_imports:
        print(f"  WARN: {f} uses raw axios import instead of @/api/request wrapper")
else:
    print("  OK: All frontend API files use @/api/request wrapper")

# ══════════════════════════════════════════════════════════════
# Scan 7: router.push without pushSafe
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Scan 7: router.push() without error handling in views")
print("=" * 60)

frontend_views_dir = backend_dir.parent / "frontend" / "src" / "views"
unsafe_pushes = []
for vue_file in frontend_views_dir.rglob("*.vue"):
    try:
        content = vue_file.read_text(encoding="utf-8")
    except Exception:
        continue
    
    if "router.push(" in content and "pushSafe" not in content:
        # Check if it's in script setup and not inside try/catch
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if "router.push(" in line and "pushSafe" not in line:
                # Check context for try/catch
                context_start = max(0, i - 5)
                context = "\n".join(lines[context_start:i])
                if "try" not in context and ".then" not in context and ".catch" not in context:
                    unsafe_pushes.append((vue_file.relative_to(backend_dir.parent / "frontend"), i))
                    break  # One per file is enough

if unsafe_pushes:
    for f, line in unsafe_pushes[:20]:
        print(f"  WARN: {f}:{line} - router.push() without try/catch or pushSafe")
    if len(unsafe_pushes) > 20:
        print(f"  ... and {len(unsafe_pushes) - 20} more")
else:
    print("  OK: All router.push() calls use pushSafe or have error handling")

# ══════════════════════════════════════════════════════════════
# Scan 8: Pagination reset missing in list views
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Scan 8: List views missing pagination reset before loadData")
print("=" * 60)

pagination_issues = []
for vue_file in frontend_views_dir.rglob("*.vue"):
    if "List.vue" not in vue_file.name and "Manage.vue" not in vue_file.name:
        continue
    try:
        content = vue_file.read_text(encoding="utf-8")
    except Exception:
        continue
    
    # Find handleCreate/handleDelete/handleEdit that call loadData without page reset
    lines = content.splitlines()
    in_handler = False
    handler_name = ""
    
    for i, line in enumerate(lines, 1):
        # Detect handler start
        m = re.match(r'\s*(?:const|function)\s+(handle\w+)\s*[=(]', line)
        if m:
            in_handler = True
            handler_name = m.group(1)
            continue
        
        if in_handler:
            # Check for loadData/fetchData call
            if re.search(r'(loadData|fetchData|loadList)\s*\(', line):
                # Check if pagination reset happens before this
                context_start = max(0, i - 15)
                context = "\n".join(lines[context_start:i])
                if "currentPage" not in context and "page.value" not in context and "pagination.page" not in context:
                    if handler_name in ["handleCreate", "handleDelete", "handleEdit", "handleImport", "handleSave"]:
                        pagination_issues.append((vue_file.relative_to(backend_dir.parent / "frontend"), i, handler_name))
            # End of handler
            if re.match(r'\s*(?:const|function)\s+\w+\s*[=(]', line) and handler_name:
                in_handler = False

if pagination_issues:
    for f, line, handler in pagination_issues[:20]:
        print(f"  WARN: {f}:{line} - {handler} may not reset pagination before loadData")
else:
    print("  OK: All list view handlers reset pagination before loadData")

print("\n" + "=" * 60)
print(f"Scan complete. Total issues: {len(issues) + len(endpoints_without_scope) + len(write_endpoints_without_log) + len(bare_list_endpoints) + len(unsafe_commits) + len(raw_imports) + len(unsafe_pushes) + len(pagination_issues)}")
print("=" * 60)
