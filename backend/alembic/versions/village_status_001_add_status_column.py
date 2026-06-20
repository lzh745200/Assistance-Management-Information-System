"""add status column to villages

Revision ID: village_status_001
Revises: rev_tier_bool_001
Create Date: 2026-06-19 18:00:00

迁移 _migrate_missing_columns 的职责至纯 Alembic——
将 villages.status 列添加为显式迁移。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "village_status_001"
down_revision = "rev_tier_bool_001"
branch_labels = None
depends_on = None


def upgrade():
    """Add status column to villages table."""
    op.add_column(
        "villages",
        sa.Column(
            "status",
            sa.String(50),
            nullable=True,
            server_default=sa.text("'active'"),
            comment="状态: active/inactive/developing/completed",
        ),
    )
    # 为现有行设置默认值
    op.execute("UPDATE villages SET status = 'active' WHERE status IS NULL")


def downgrade():
    """Remove status column from villages table."""
    with op.batch_alter_table("villages") as batch_op:
        batch_op.drop_column("status")
