"""Check all files using safe_commit have the import."""
import os

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'api', 'v1')
missing = []

for root, dirs, files in os.walk(BACKEND_DIR):
    for f in files:
        if not f.endswith('.py'):
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding='utf-8') as fh:
            content = fh.read()
        if 'safe_commit(db)' in content and 'from app.core.transaction import safe_commit' not in content:
            missing.append(fp)

if missing:
    print("MISSING IMPORTS:")
    for m in missing:
        print(f"  {m}")
else:
    print("All files have safe_commit import")
