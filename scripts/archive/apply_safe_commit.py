"""
自动化将裸 db.commit() 替换为 safe_commit(db)，并添加导入。
简单直接：替换所有 db.commit() 调用，safe_commit 内部已有回滚保护。
"""
import re
import os

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'api', 'v1')

TARGET_FILES = [
    'fund_lifecycle.py',
    'school.py',
    'policy.py',
    'report_templates.py',
    'supported_village.py',
    'projects.py',
    'funds.py',
    'auth/users.py',
    'auth/user_management.py',
    'organization.py',
    'project_milestones.py',
    'fund_budgets.py',
    'work_logs.py',
    'todos.py',
    'validation.py',
    'system/audit.py',
    'system/zero_trust.py',
    'system/update_logs.py',
    'approval.py',
    'feedback.py',
    'encryption.py',
    'machine_code.py',
    'menus.py',
    'map.py',
    'system_config.py',
    'system_health.py',
    'auth/auth.py',
    'data/data/dashboard.py',
    'data/data/data_packages.py',
    'data/data/reports.py',
    'data/data/data_reports.py',
]

IMPORT_LINE = "from app.core.transaction import safe_commit"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changes = 0

    # Skip if safe_commit already imported
    if 'safe_commit' in content and IMPORT_LINE in content:
        return 0

    # Replace all db.commit() with safe_commit(db)
    # But skip lines that already have safe_commit
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if 'db.commit()' in line and 'safe_commit' not in line:
            new_line = line.replace('db.commit()', 'safe_commit(db)')
            new_lines.append(new_line)
            changes += 1
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    # Add import if we made changes
    if changes > 0 and IMPORT_LINE not in content:
        # Find the last import from app. line
        import_pattern = r'((?:from app\.)[^\n]+\n)'
        matches = list(re.finditer(import_pattern, content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            content = content[:insert_pos] + IMPORT_LINE + '\n' + content[insert_pos:]
        else:
            # Find any import block
            import_pattern2 = r'((?:from |import )[^\n]+\n)+'
            matches2 = list(re.finditer(import_pattern2, content))
            if matches2:
                last_match = matches2[-1]
                insert_pos = last_match.end()
                content = content[:insert_pos] + IMPORT_LINE + '\n' + content[insert_pos:]
            else:
                content = IMPORT_LINE + '\n' + content

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {filepath}: {changes} commits replaced")

    return changes

def main():
    total_changes = 0
    for filename in TARGET_FILES:
        filepath = os.path.join(BACKEND_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filename}")
            continue
        total_changes += process_file(filepath)

    print(f"\nTotal: {total_changes} db.commit() -> safe_commit(db) replacements")

if __name__ == '__main__':
    main()
