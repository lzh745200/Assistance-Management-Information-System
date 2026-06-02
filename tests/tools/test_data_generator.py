"""
测试数据生成器

用于生成测试所需的各类数据

使用方法：
python tests/tools/test_data_generator.py
"""

import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
from faker import Faker

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.village import Village
from app.models.project import Project
from app.models.organization import Organization
from app.core.security import get_password_hash


fake = Faker('zh_CN')


class TestDataGenerator:
    """测试数据生成器"""

    def __init__(self):
        self.db = SessionLocal()

    def __del__(self):
        self.db.close()

    def generate_users(self, count=10):
        """生成测试用户"""
        print(f"生成 {count} 个测试用户...")

        users = []
        for i in range(count):
            user = User(
                username=f"test_user_{i+1}",
                password=get_password_hash("test123456"),
                full_name=fake.name(),
                email=fake.email(),
                role="user" if i < count - 2 else "admin",
                is_active=True
            )
            users.append(user)

        self.db.add_all(users)
        self.db.commit()

        print(f"✓ 成功生成 {count} 个用户")
        return users

    def generate_organizations(self, count=5):
        """生成测试组织"""
        print(f"生成 {count} 个测试组织...")

        organizations = []
        org_types = ["军队单位", "地方政府", "企业", "社会组织"]

        for i in range(count):
            org = Organization(
                name=f"{fake.company()}{random.choice(['集团', '公司', '单位'])}",
                code=f"ORG{i+1:04d}",
                type=random.choice(org_types),
                level=random.randint(1, 4),
                contact_person=fake.name(),
                contact_phone=fake.phone_number(),
                address=fake.address(),
                description=fake.text(max_nb_chars=100)
            )
            organizations.append(org)

        self.db.add_all(organizations)
        self.db.commit()

        print(f"✓ 成功生成 {count} 个组织")
        return organizations

    def generate_villages(self, count=20):
        """生成测试帮扶村"""
        print(f"生成 {count} 个测试帮扶村...")

        villages = []
        provinces = ["河北省", "山西省", "内蒙古", "辽宁省", "吉林省"]

        for i in range(count):
            province = random.choice(provinces)
            village = Village(
                name=f"{fake.city()}{fake.street_name()}村",
                code=f"VIL{i+1:04d}",
                province=province,
                city=fake.city(),
                county=fake.district(),
                township=f"{fake.street_name()}乡",
                village_type=random.choice(["贫困村", "脱贫村", "示范村"]),
                poverty_level=random.choice(["深度贫困", "一般贫困", "已脱贫"]),
                population=random.randint(500, 5000),
                households=random.randint(100, 1000),
                poor_households=random.randint(10, 200),
                area=round(random.uniform(5.0, 50.0), 2),
                contact_person=fake.name(),
                contact_phone=fake.phone_number(),
                description=fake.text(max_nb_chars=200)
            )
            villages.append(village)

        self.db.add_all(villages)
        self.db.commit()

        print(f"✓ 成功生成 {count} 个帮扶村")
        return villages

    def generate_projects(self, count=30, villages=None):
        """生成测试项目"""
        print(f"生成 {count} 个测试项目...")

        if not villages:
            villages = self.db.query(Village).limit(20).all()

        if not villages:
            print("错误：没有可用的帮扶村，请先生成帮扶村数据")
            return []

        projects = []
        project_types = ["基础设施", "产业发展", "教育扶贫", "医疗扶贫", "文化建设"]
        statuses = ["planning", "approved", "in_progress", "completed"]

        for i in range(count):
            start_date = datetime.now() - timedelta(days=random.randint(0, 365))
            end_date = start_date + timedelta(days=random.randint(90, 730))

            project = Project(
                name=f"{fake.catch_phrase()}{random.choice(['项目', '工程', '计划'])}",
                code=f"PRJ{i+1:04d}",
                type=random.choice(project_types),
                village_id=random.choice(villages).id,
                budget=round(random.uniform(10000, 1000000), 2),
                actual_cost=round(random.uniform(8000, 900000), 2),
                start_date=start_date,
                end_date=end_date,
                status=random.choice(statuses),
                progress=random.randint(0, 100),
                description=fake.text(max_nb_chars=200),
                expected_benefit=fake.text(max_nb_chars=100)
            )
            projects.append(project)

        self.db.add_all(projects)
        self.db.commit()

        print(f"✓ 成功生成 {count} 个项目")
        return projects

    def generate_all(self):
        """生成所有测试数据"""
        print("=" * 50)
        print("开始生成测试数据...")
        print("=" * 50)

        # 生成组织
        organizations = self.generate_organizations(5)

        # 生成用户
        users = self.generate_users(10)

        # 生成帮扶村
        villages = self.generate_villages(20)

        # 生成项目
        projects = self.generate_projects(30, villages)

        print("=" * 50)
        print("测试数据生成完成！")
        print(f"组织：{len(organizations)} 个")
        print(f"用户：{len(users)} 个")
        print(f"帮扶村：{len(villages)} 个")
        print(f"项目：{len(projects)} 个")
        print("=" * 50)

    def clear_test_data(self):
        """清理测试数据"""
        print("清理测试数据...")

        # 删除测试用户
        self.db.query(User).filter(User.username.like("test_user_%")).delete(synchronize_session=False)

        # 删除测试项目
        self.db.query(Project).filter(Project.code.like("PRJ%")).delete(synchronize_session=False)

        # 删除测试帮扶村
        self.db.query(Village).filter(Village.code.like("VIL%")).delete(synchronize_session=False)

        # 删除测试组织
        self.db.query(Organization).filter(Organization.code.like("ORG%")).delete(synchronize_session=False)

        self.db.commit()

        print("✓ 测试数据清理完成")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试数据生成器")
    parser.add_argument("--clear", action="store_true", help="清理测试数据")
    parser.add_argument("--users", type=int, default=10, help="生成用户数量")
    parser.add_argument("--villages", type=int, default=20, help="生成帮扶村数量")
    parser.add_argument("--projects", type=int, default=30, help="生成项目数量")

    args = parser.parse_args()

    generator = TestDataGenerator()

    if args.clear:
        generator.clear_test_data()
    else:
        generator.generate_all()


if __name__ == "__main__":
    main()
