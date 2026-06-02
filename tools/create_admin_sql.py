"""直接用SQL创建管理员账户"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.security import hash_password
from datetime import datetime

# 数据库路径
db_path = "backend/data/rural_revitalization.db"

# 生成密码哈希
password = "Admin123!"
hashed = hash_password(password)

print(f"创建管理员账户...")
print(f"用户名: admin")
print(f"密码: {password}")
print(f"哈希: {hashed}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表结构
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"\n数据库列: {', '.join(column_names)}")

# 检查是否已有admin用户
cursor.execute("SELECT id, username FROM users WHERE username='admin'")
existing = cursor.fetchone()

if existing:
    print(f"\nadmin 用户已存在 (ID: {existing[0]})，更新密码...")

    # 检查是用 password_hash 还是 hashed_password
    if 'password_hash' in column_names:
        cursor.execute("""
            UPDATE users
            SET password_hash = ?,
                is_active = 1,
                failed_login_count = 0,
                locked_until = NULL
            WHERE username = 'admin'
        """, (hashed,))
    else:
        cursor.execute("""
            UPDATE users
            SET hashed_password = ?,
                is_active = 1,
                failed_login_count = 0,
                locked_until = NULL
            WHERE username = 'admin'
        """, (hashed,))

    conn.commit()
    print("✓ 密码已更新")
else:
    print("\n创建新的 admin 用户...")

    # 根据表结构插入
    if 'password_hash' in column_names:
        cursor.execute("""
            INSERT INTO users (
                username, email, password_hash, full_name, role,
                is_active, is_superuser, failed_login_count,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin',
            'admin@example.com',
            hashed,
            '系统管理员',
            'super_admin',
            1,
            1,
            0,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    else:
        cursor.execute("""
            INSERT INTO users (
                username, email, hashed_password, full_name, role,
                is_active, is_superuser, failed_login_count,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'admin',
            'admin@example.com',
            hashed,
            '系统管理员',
            'super_admin',
            1,
            1,
            0,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

    conn.commit()
    print("✓ 用户创建成功")

# 验证
cursor.execute("SELECT username, email, role, is_active FROM users WHERE username='admin'")
admin = cursor.fetchone()

if admin:
    print("\n" + "=" * 80)
    print("管理员账户信息:")
    print("=" * 80)
    print(f"用户名: {admin[0]}")
    print(f"邮箱: {admin[1]}")
    print(f"角色: {admin[2]}")
    print(f"激活: {admin[3]}")
    print("=" * 80)
    print(f"\n✓ 登录凭据:")
    print(f"  用户名: admin")
    print(f"  密码: {password}")
else:
    print("\n✗ 创建失败")

# 显示所有用户
cursor.execute("SELECT username, role, is_active FROM users")
all_users = cursor.fetchall()

print(f"\n系统共有 {len(all_users)} 个用户:")
for user in all_users:
    print(f"  - {user[0]:15} 角色: {user[1]:15} 激活: {user[2]}")

conn.close()
