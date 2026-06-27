#!/usr/bin/env python3
"""检查学校数据"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.school import School

db = SessionLocal()
try:
    schools = db.query(School).all()
    print(f"学校数量: {len(schools)}")
    for school in schools:
        print(f"  ID: {school.id}, 名称: {school.name}, 地址: {school.address}, 状态: {school.status}")
except Exception as e:
    print(f"查询错误: {e}")
finally:
    db.close()

# 检查其他可能包含学校统计的表
try:
    from app.models.organization import Organization
    from app.models.project import Project
    from app.models.supported_village import SupportedVillage

    db2 = SessionLocal()
    orgs = db2.query(Organization).all()
    print(f"\n组织数量: {len(orgs)}")
    for org in orgs[:5]:
        print(f"  组织ID: {org.id}, 名称: {org.name}, 父ID: {org.parent_id}")

    projects = db2.query(Project).all()
    print(f"\n项目数量: {len(projects)}")

    villages = db2.query(SupportedVillage).all()
    print(f"\n帮扶村数量: {len(villages)}")
    db2.close()
except Exception as e:
    print(f"其他查询错误: {e}")
