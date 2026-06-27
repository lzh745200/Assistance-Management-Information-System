"""Common factory fixtures — base entities used across tests."""

from datetime import datetime, timezone

from app.models.region import Region
from app.models.organization import Organization
from app.models.rbac import BasicRole as Role
from app.models.policy import Policy, PolicyCategory


class RegionFactory:
    @staticmethod
    def create(db, name="贵州省", code="520000", level="province", parent_code=None):
        now = datetime.now(timezone.utc)
        obj = Region(
            name=name,
            code=code,
            level=level,
            parent_code=parent_code,
            created_at=now,
            updated_at=now,
        )
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(name="贵州省", code="520000", level="province", created_at=now, updated_at=now)
        data.update(kwargs)
        return Region(**data)


class OrganizationFactory:
    @staticmethod
    def create(db, name="测试单位", code="ORG001", level="level_1", parent_id=None, org_type="department"):
        now = datetime.now(timezone.utc)
        obj = Organization(
            name=name,
            code=code,
            level=level,
            parent_id=parent_id,
            org_type=org_type,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(name="测试单位", code="ORG001", level="level_1", is_active=True,
                     created_at=now, updated_at=now)
        data.update(kwargs)
        return Organization(**data)


class RoleFactory:
    _id_counter = 0

    @staticmethod
    def _next_id():
        RoleFactory._id_counter += 1
        return f"role-{RoleFactory._id_counter:04d}"

    @staticmethod
    def create(db, name="测试角色", description="测试角色描述", priority=100):
        now = datetime.now(timezone.utc)
        obj = Role(
            id=RoleFactory._next_id(),
            name=name,
            description=description,
            is_system=False,
            is_active=True,
            priority=priority,
            created_at=now,
            updated_at=now,
        )
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            id=RoleFactory._next_id(),
            name="测试角色",
            description="测试角色描述",
            is_system=False,
            is_active=True,
            priority=100,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return Role(**data)


class PolicyFactory:
    @staticmethod
    def create(db, title="测试政策", content="测试政策内容", category="乡村振兴",
               summary="政策摘要", issue_date=None, status="published"):
        now = datetime.now(timezone.utc)
        obj = Policy(
            title=title,
            content=content,
            summary=summary,
            category=category,
            issue_date=issue_date or now,
            status=status,
            is_important=False,
            view_count=0,
            download_count=0,
            created_at=now,
            updated_at=now,
        )
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            title="测试政策", content="测试政策内容", summary="政策摘要",
            category="乡村振兴", issue_date=now, status="published",
            is_important=False, view_count=0, download_count=0,
            created_at=now, updated_at=now,
        )
        data.update(kwargs)
        return Policy(**data)


class PolicyCategoryFactory:
    @staticmethod
    def create(db, name="乡村振兴", code="rural_revitalization", sort_order=1, parent_id=None):
        now = datetime.now(timezone.utc)
        obj = PolicyCategory(
            name=name, code=code, sort_order=sort_order,
            parent_id=parent_id, is_active=True,
            created_at=now, updated_at=now,
        )
        db.add(obj)
        db.flush()
        return obj
