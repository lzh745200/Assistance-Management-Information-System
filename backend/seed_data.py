#!/usr/bin/env python
"""种子数据脚本 — 为所有业务模块生成测试数据"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.supported_village import SupportedVillage
from app.models.school import School
from app.models.project import Project
from app.models.fund import Fund
from app.models.policy import Policy, PolicyCategory
from app.core.security import hash_password
from datetime import date, datetime, timezone

db = SessionLocal()
now = datetime.now(timezone.utc)

print("=== Seeding test data ===\n")

# 1. Organizations
orgs_data = [
    ("某部队政治工作部", "ORG-001", "military"),
    ("某部队后勤保障部", "ORG-002", "military"),
    ("黔南州乡村振兴局", "ORG-003", "government"),
    ("龙里县农业农村局", "ORG-004", "government"),
]
for name, code, otype in orgs_data:
    if not db.query(Organization).filter(Organization.code == code).first():
        db.add(Organization(name=name, code=code, org_type=otype))
db.commit()
print(f"[OK] Organizations: {db.query(Organization).count()}")

# 2. Users
users_data = [
    ("admin", "系统管理员", "admin", "admin123"),
    ("zhangsan", "张三", "manager", "123456"),
    ("lisi", "李四", "user", "123456"),
    ("wangwu", "王五", "user", "123456"),
]
for uname, full, role, pw in users_data:
    u = db.query(User).filter(User.username == uname).first()
    if not u:
        u = User(username=uname, full_name=full, role=role, is_active=True, created_at=now)
        db.add(u)
    u.hashed_password = hash_password(pw)
    u.is_active = True
db.commit()
print(f"[OK] Users: {db.query(User).count()}")

# 3. Villages
villages_data = [
    ("红旗村", "某部队政治工作部", "某部队", "贵州省", "黔南州", "都匀市", "墨冲镇", 1),
    ("红星村", "某部队后勤保障部", "某部队", "贵州省", "黔南州", "都匀市", "平浪镇", 2),
    ("前进村", "某部队政治工作部", "某部队", "贵州省", "黔南州", "独山县", "麻尾镇", 3),
    ("光明村", "某部队后勤保障部", "某部队", "贵州省", "黔南州", "贵定县", "昌明镇", 4),
    ("幸福村", "某部队政治工作部", "某部队", "贵州省", "黔南州", "龙里县", "谷脚镇", 5),
]
for vn, dept, unit, prov, city, county, town, seq in villages_data:
    if not db.query(SupportedVillage).filter(SupportedVillage.village_name == vn).first():
        db.add(SupportedVillage(village_name=vn, department=dept, support_unit=unit,
                province=prov, city=city, county=county, township=town, sequence_no=seq))
db.commit()
print(f"[OK] Villages: {db.query(SupportedVillage).count()}")

# 4. Schools
schools_data = [
    ("红星希望小学", "小学", "贵州省", "黔南州", "都匀市", "陈老师", 320, 18, "某部队", "active"),
    ("前进中学", "初中", "贵州省", "黔南州", "独山县", "刘校长", 580, 42, "某部队", "active"),
    ("光明小学", "小学", "贵州省", "黔南州", "贵定县", "黄老师", 210, 12, "某部队", "active"),
]
for name, stype, prov, city, dist, principal, sc, tc, unit, status in schools_data:
    if not db.query(School).filter(School.name == name).first():
        db.add(School(name=name, type=stype, province=prov, city=city, district=dist,
                principal=principal, student_count=sc, teacher_count=tc,
                support_unit=unit, support_status=status, created_at=now))
db.commit()
print(f"[OK] Schools: {db.query(School).count()}")

# 5. Projects
villages = db.query(SupportedVillage).all()
projects_data = [
    ("村内道路硬化工程", "XM-2024-001", "基础设施", "in_progress", 150.0, 85, date(2024,3,1), date(2024,12,31), "张三", "某部队政治工作部"),
    ("安全饮水工程", "XM-2024-002", "基础设施", "completed", 80.0, 100, date(2024,1,15), date(2024,8,15), "李四", "某部队后勤保障部"),
    ("特色种植示范基地", "XM-2024-003", "产业发展", "in_progress", 200.0, 60, date(2024,5,1), date(2025,4,30), "王五", "某部队政治工作部"),
    ("电商服务中心建设", "XM-2024-004", "产业发展", "planning", 120.0, 15, date(2024,8,1), date(2025,6,30), "张三", "某部队后勤保障部"),
    ("文化活动室建设", "XM-2024-005", "公共服务", "completed", 60.0, 100, date(2024,2,1), date(2024,9,30), "李四", "某部队政治工作部"),
    ("太阳能路灯安装", "XM-2024-006", "基础设施", "in_progress", 45.0, 70, date(2024,6,1), date(2024,11,30), "王五", "某部队后勤保障部"),
]
for i, (name, code, ptype, status, budget, prog, sd, ed, rp, ru) in enumerate(projects_data):
    if not db.query(Project).filter(Project.code == code).first():
        v = villages[i % len(villages)] if villages else None
        db.add(Project(name=name, code=code, type=ptype, status=status, budget=budget,
                progress=prog, start_date=sd, end_date=ed,
                responsible_person=rp, responsible_unit=ru,
                village_id=v.id if v else None, created_at=now))
db.commit()
print(f"[OK] Projects: {db.query(Project).count()}")

# 6. Funds
projects = db.query(Project).all()
funds_data = [
    ("第一季度帮扶资金", "ZJ-2024-001", 100.0, "project", "military", "approved", date(2024,3,15), "张三", "道路硬化工程款"),
    ("饮水工程专项经费", "ZJ-2024-002", 80.0, "infrastructure", "military", "completed", date(2024,2,1), "李四", "安全饮水工程"),
    ("产业帮扶资金", "ZJ-2024-003", 200.0, "project", "government", "allocated", date(2024,5,10), "王五", "种植示范基地建设"),
    ("办公设备采购", "ZJ-2024-004", 30.0, "operation", "military", "pending", date(2024,7,1), "张三", "村委会办公设备"),
    ("教育培训经费", "ZJ-2024-005", 50.0, "education", "government", "in_use", date(2024,4,20), "李四", "村民技能培训"),
]
for i, (name, code, amt, ftype, fsrc, status, dt, op, purpose) in enumerate(funds_data):
    if not db.query(Fund).filter(Fund.code == code).first():
        p = projects[i % len(projects)] if projects else None
        db.add(Fund(name=name, code=code, amount=amt, fund_type=ftype, fund_source=fsrc,
                status=status, date=dt, operator=op, purpose=purpose,
                project_id=p.id if p else None, project_name=p.name if p else None,
                created_at=now))
db.commit()
print(f"[OK] Funds: {db.query(Fund).count()}")

# 7. Policy Categories + Policies
cats = ["军队帮扶政策", "地方政府政策", "国家乡村振兴政策", "教育帮扶政策", "产业帮扶政策"]
for c in cats:
    if not db.query(PolicyCategory).filter(PolicyCategory.name == c).first():
        db.add(PolicyCategory(name=c))
db.commit()

cats_map = {c.name: c.id for c in db.query(PolicyCategory).all()}
policies_data = [
    ("关于全面推进乡村振兴的意见", "国家乡村振兴政策", "国家级", "published", date(2024,1,15)),
    ("军队参与乡村振兴工作实施办法", "军队帮扶政策", "军队级", "published", date(2024,2,20)),
    ("贵州省乡村振兴促进条例", "地方政府政策", "省级", "published", date(2024,3,10)),
    ("教育帮扶专项资金管理办法", "教育帮扶政策", "国家级", "published", date(2024,4,5)),
    ("产业帮扶示范基地建设标准", "产业帮扶政策", "省级", "draft", date(2024,5,1)),
]
for title, cat, level, status, pdate in policies_data:
    if not db.query(Policy).filter(Policy.title == title).first():
        db.add(Policy(title=title, category_id=cats_map.get(cat), level=level,
                status=status, publish_date=pdate, created_at=now))
db.commit()
print(f"[OK] Policies: {db.query(Policy).count()} (Categories: {len(cats)})")

db.close()
print("\n=== Seed Complete ===")
print("Accounts: admin/admin123, zhangsan/123456, lisi/123456, wangwu/123456")
