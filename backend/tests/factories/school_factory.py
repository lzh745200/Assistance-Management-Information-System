"""School model factories."""

from datetime import datetime, timezone

from app.models.school import School, SchoolSupport, SchoolProject, ScholarshipStudent


class SchoolFactory:
    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            name="测试学校",
            code="SCH-" + str(id(now))[-6:],
            type="小学",
            province="贵州省",
            city="贵阳市",
            district="测试县",
            address="测试地址",
            principal="校长",
            contact_phone="0851-1234567",
            student_count=500,
            teacher_count=30,
            support_status="supported",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return School(**data)

    @staticmethod
    def create(db, **kwargs):
        obj = SchoolFactory.build(**kwargs)
        db.add(obj)
        db.flush()
        return obj


class SchoolSupportFactory:
    @staticmethod
    def build(school_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            school_id=school_id,
            support_type="设备捐赠",
            amount=100000,
            description="教学设备捐赠",
            support_date=now,
            created_at=now,
        )
        data.update(kwargs)
        return SchoolSupport(**data)

    @staticmethod
    def create(db, school_id=1, **kwargs):
        obj = SchoolSupportFactory.build(school_id=school_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class SchoolProjectFactory:
    @staticmethod
    def build(school_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            school_id=school_id,
            name="校园改造项目",
            phase="planning",
            category="infrastructure",
            description="改善教学环境",
            budget=500000.00,
            actual_cost=300000.00,
            start_date=now,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return SchoolProject(**data)

    @staticmethod
    def create(db, school_id=1, **kwargs):
        obj = SchoolProjectFactory.build(school_id=school_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class ScholarshipStudentFactory:
    @staticmethod
    def build(school_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            school_id=school_id,
            student_name="张三",
            grade="三年级",
            year=2024,
            amount=2000.00,
            reason="品学兼优",
            status="active",
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return ScholarshipStudent(**data)

    @staticmethod
    def create(db, school_id=1, **kwargs):
        obj = ScholarshipStudentFactory.build(school_id=school_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj
