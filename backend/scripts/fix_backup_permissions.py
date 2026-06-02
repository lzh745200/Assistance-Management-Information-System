#!/usr/bin/env python3
"""批量替换 backup.py 中的权限检查代码"""

import re

file_path = r"C:\military-Rural Revitalization-system\backend\app\api\v1\backup.py"

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换模式 1: 管理员权限检查
pattern1 = r'''    # 权限检查
    if current_user\.role not in \["super_admin", "admin"\]:
        raise HTTPException\(
            status_code=status\.HTTP_403_FORBIDDEN, detail="只有管理员可以.*?"\
        \)'''

replacement1 = '    require_admin(current_user, "只有管理员可以查看备份状态")'

# 执行替换
content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

# 针对不同的错误消息进行多次替换
replacements = [
    (r'require_admin\(current_user, "只有管理员可以查看备份状态"\)',
     lambda m: 'require_admin(current_user, "只有管理员可以查看备份状态")'),
    (r'require_admin\(current_user, "只有管理员可以.*?"\)',
     lambda m: m.group(0)),  # 保持已有的
]

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 已更新 backup.py")
