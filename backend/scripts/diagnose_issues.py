#!/usr/bin/env python3
"""诊断问题脚本"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.school import School
from app.models.organization import Organization
from app.core.security import verify_password

db = SessionLocal()

try:
    print("=" * 60)
    print("1. 检查管理员用户信息")
    print("=" * 60)
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print(f"  ID: {admin.id}")
        print(f"  用户名: {admin.username}")
        print(f"  角色: {admin.role}")
        print(f"  是否超级用户: {admin.is_superuser}")
        print(f"  组织ID: {admin.organization_id}")
        print(f"  部门: {admin.department}")
    else:
        print("  未找到管理员用户")

    print("\n" + "=" * 60)
    print("2. 检查学校数据")
    print("=" * 60)
    schools = db.query(School).all()
    print(f"  学校总数: {len(schools)}")
    for school in schools:
        print(f"\n  ID: {school.id}")
        print(f"  名称: {school.name}")
        print(f"  是否激活: {school.is_active}")
        print(f"  帮扶单位: {school.support_unit}")
        print(f"  帮扶状态: {school.support_status}")

    print("\n" + "=" * 60)
    print("3. 检查组织数据")
    print("=" * 60)
    orgs = db.query(Organization).all()
    print(f"  组织总数: {len(orgs)}")
    for org in orgs:
        print(f"  ID: {org.id}, 名称: {org.name}, 父ID: {org.parent_id}")

    print("\n" + "=" * 60)
    print("4. 模拟API查询")
    print("=" * 60)

    # 模拟学校API查询
    query = db.query(School).filter(School.is_active == True)
    total = query.count()
    print(f"  激活学校数（无数据范围过滤）: {total}")

    # 检查用户权限逻辑
    if admin:
        is_admin_role = admin.role in ("admin", "super_admin")
        print(f"\n  管理员角色检查:")
        print(f"    角色: {admin.role}")
        print(f"    is_admin_role: {is_admin_role}")
        print(f"    is_superuser: {admin.is_superuser}")

    print("\n" + "=" * 60)
    print("5. 检查问题原因")
    print("=" * 60)

    # 检查学校support_unit
    for school in schools:
        if not school.support_unit:
            print(f"  警告: 学校 '{school.name}' 没有设置帮扶单位")

    # 检查组织为空的问题
    if len(orgs) == 0:
        print("\n  严重: 组织表为空！这会导致：")
        print("    - 用户与组织管理页面404错误")
        print("    - 非管理员用户无法看到任何数据")
        print("\n  需要创建至少一个组织，并将用户分配到该组织")

    # 检查is_active
    inactive_schools = db.query(School).filter(School.is_active == False).all()
    if inactive_schools:
        print(f"\n  注意: 有 {len(inactive_schools)} 所未激活的学校")
        for s in inactive_schools:
            print(f"    - {s.name}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
