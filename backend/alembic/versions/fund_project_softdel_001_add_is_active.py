"""add is_active column to funds and projects for soft delete

Revision ID: fund_project_softdel_001
Revises: village_softdel_001, 012_consolidate_baseline
Create Date: 2026-07-14 12:00:00

为 funds 和 projects 表增加 is_active 软删字段，与 supported_villages/schools 一致。
默认 True，删除操作置 False（软删），列表默认过滤，详情可见。
同时合并 012_consolidate_baseline 分支到主链。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fund_project_softdel_001"
down_revision = ("village_softdel_001", "012_consolidate_baseline")
branch_labels = None
depends_on = None


def upgrade():
    """Add is_active column to funds and projects tables."""
    # ── funds 表 ──
    op.add_column(
        "funds",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
            comment="是否启用(软删标记)",
        ),
    )
    op.execute("UPDATE funds SET is_active = 1 WHERE is_active IS NULL")
    op.create_index("ix_funds_is_active", "funds", ["is_active"])

    # ── projects 表 ──
    op.add_column(
        "projects",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
            comment="是否启用(软删标记)",
        ),
    )
    op.execute("UPDATE projects SET is_active = 1 WHERE is_active IS NULL")
    op.create_index("ix_projects_is_active", "projects", ["is_active"])


def downgrade():
    """Remove is_active column from funds and projects tables."""
    op.drop_index("ix_projects_is_active", table_name="projects")
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("is_active")

    op.drop_index("ix_funds_is_active", table_name="funds")
    with op.batch_alter_table("funds") as batch_op:
        batch_op.drop_column("is_active")
