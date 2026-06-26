"""Common factory fixtures — base entities used across tests."""

from datetime import datetime, timezone

from app.models.region import Region
from app.models.organization import Organization
from app.models.rbac import BasicRole as Role
from app.models.policy import Policy, PolicyCategory


class RegionFactory:
    @staticmethod
    def create(db, name="贵州省", code="520000", level="province", parent_id=None):
        now = datetime.now(timezone.utc)
        obj = Region(
            name=name,
            code=code,
            level=level,
            parent_id=parent_id,
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
    @staticmethod
    def create(db, name="测试角色", code="test_role", permissions="read,write"):
        now = datetime.now(timezone.utc)
        obj = Role(name=name, code=code, permissions=permissions, created_at=now, updated_at=now)
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(name="测试角色", code="test_role", permissions="read,write",
                     created_at=now, updated_at=now)
        data.update(kwargs)
        return Role(**data)


class PolicyFactory:
    @staticmethod
    def create(db, title="测试政策", content="测试政策内容", category="乡村振兴",
               publish_date=None, status="published"):
        now = datetime.now(timezone.utc)
        obj = Policy(
            title=title,
            content=content,
            category=category,
            publish_date=publish_date or now.date(),
            status=status,
            created_at=now,
            updated_at=now,
        )
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(title="测试政策", content="测试政策内容", category="乡村振兴",
                     publish_date=now.date(), status="published",
                     created_at=now, updated_at=now)
        data.update(kwargs)
        return Policy(**data)


class PolicyCategoryFactory:
    @staticmethod
    def create(db, name="乡村振兴", code="rural_revitalization", sort_order=1):
        now = datetime.now(timezone.utc)
        obj = PolicyCategory(name=name, code=code, sort_order=sort_order,
                              created_at=now, updated_at=now)
        db.add(obj)
        db.flush()
        return obj
