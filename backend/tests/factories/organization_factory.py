"""Organization model factory."""

from datetime import datetime, timezone

from app.models.organization import Organization


class OrganizationFactory:
    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            name="测试单位",
            code="ORG-" + str(id(now))[-6:],
            level="level_1",
            org_type="department",
            is_active=True,
            sort_order=0,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return Organization(**data)

    @staticmethod
    def create(db, **kwargs):
        obj = OrganizationFactory.build(**kwargs)
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def create_tree(db, depth=3, prefix="ORG"):
        """Create a tree of organizations: root -> child -> grandchild."""
        root = OrganizationFactory.create(db, name=f"{prefix}_ROOT", level="level_1")
        child = OrganizationFactory.create(db, name=f"{prefix}_CHILD", level="level_2", parent_id=root.id)
        grandchild = OrganizationFactory.create(db, name=f"{prefix}_GC", level="level_3", parent_id=child.id)
        return root, child, grandchild
