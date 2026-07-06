"""Verify critical frontend API endpoints exist in backend."""
import os, re

def find_routes(path):
    routes = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith('.py') and not f.startswith('__'):
                full = os.path.join(root, f)
                with open(full, encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
                prefix_m = re.search(r'prefix="([^"]+)"', content)
                if not prefix_m:
                    prefix_m = re.search(r"prefix='([^']+)'", content)
                prefix = prefix_m.group(1) if prefix_m else ''
                for m in re.finditer(r'@router\.(get|post|put|delete|patch)\("([^"]+)"', content):
                    method, ep = m.group(1), m.group(2)
                    routes.append((method.upper(), prefix + ep, os.path.basename(full)))
                for m in re.finditer(r"@router\.(get|post|put|delete|patch)\('([^']+)'", content):
                    method, ep = m.group(1), m.group(2)
                    routes.append((method.upper(), prefix + ep, os.path.basename(full)))
    return routes

routes = find_routes('backend/app/api/v1')

endpoints_to_check = [
    ('GET', '/dashboard/stats'),
    ('POST', '/data-quality/check'),
    ('GET', '/data-quality/check/issues'),
    ('POST', '/data-quality/fix'),
    ('GET', '/help/articles'),
    ('POST', '/rbac/assign/role'),
    ('DELETE', '/rbac/revoke/role'),
    ('GET', '/rbac/roles'),
    ('GET', '/system/audit/logs'),
    ('POST', '/funds/apply'),
    ('GET', '/rural-works/report/generate'),
    ('GET', '/supported-villages'),
    ('GET', '/projects'),
    ('GET', '/schools'),
    ('GET', '/funds'),
    ('GET', '/policies'),
    ('POST', '/policies'),
    ('GET', '/effectiveness/evaluate'),
    ('GET', '/effectiveness/rankings'),
    ('GET', '/machine-code/admin/list'),
    ('POST', '/machine-code/organization/create'),
]

all_routes = [(m, p, f) for m, p, f in routes]

print(f"Total backend routes: {len(all_routes)}")
print()
for method, path in endpoints_to_check:
    found = [r for r in all_routes if r[0] == method and (r[1] == path or r[1].startswith(path + '/'))]
    if found:
        print(f"  OK: {method:6s} {path:45s} -> {found[0][1]} ({found[0][2]})")
    else:
        print(f"  MISS: {method:6s} {path:45s} *** NOT FOUND IN BACKEND ***")
