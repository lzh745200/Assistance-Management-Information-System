"""revitalization_tier to bool + remove tiered_development_level

Revision ID: rev_tier_bool_001
Revises: 92220c9a69a5
Create Date: 2026-06-08

将 revitalization_tier (String) 重命名为 is_revitalization_tier (Boolean)
删除 tiered_development_level 列
删除 tiered_development_levels 表
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "rev_tier_bool_001"
down_revision: Union[str, None] = "92220c9a69a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 删除旧索引
    op.drop_index("ix_supported_villages_tier", table_name="supported_villages", if_exists=True)
    op.drop_index("ix_villages_province_tier", table_name="supported_villages", if_exists=True)
    op.drop_index("ix_villages_county_tier", table_name="supported_villages", if_exists=True)

    # 2. 删除 tiered_development_level 列
    op.drop_column("supported_villages", "tiered_development_level")

    # 3. 添加 is_revitalization_tier 列 (Boolean, 默认 False)
    op.add_column(
        "supported_villages",
        sa.Column("is_revitalization_tier", sa.Boolean(), nullable=True, server_default="0"),
    )

    # 4. 将旧 revitalization_tier 数据迁移到新列 (有值的视为 True)
    op.execute(
        "UPDATE supported_villages SET is_revitalization_tier = 1 "
        "WHERE revitalization_tier IS NOT NULL AND revitalization_tier != ''"
    )
    # 其余行设为 False
    op.execute(
        "UPDATE supported_villages SET is_revitalization_tier = 0 "
        "WHERE is_revitalization_tier IS NULL"
    )

    # 5. 删除旧 revitalization_tier 列
    # SQLite 不支持 DROP COLUMN，用表重建方式
    # 但 alembic batch mode 会自动处理
    with op.batch_alter_table("supported_villages") as batch_op:
        batch_op.drop_column("revitalization_tier")

    # 6. 设置为 NOT NULL 并移除 server_default
    with op.batch_alter_table("supported_villages") as batch_op:
        batch_op.alter_column("is_revitalization_tier", nullable=False, server_default=None)

    # 7. 删除 tiered_development_levels 表
    op.drop_table("tiered_development_levels", if_exists=True)


def downgrade() -> None:
    # 重建 revitalization_tier (String) 列
    op.add_column(
        "supported_villages",
        sa.Column("revitalization_tier", sa.String(50), nullable=True),
    )

    # 重建 tiered_development_level 列
    op.add_column(
        "supported_villages",
        sa.Column("tiered_development_level", sa.String(50), nullable=True),
    )

    # 重建 tiered_development_levels 表
    op.create_table(
        "tiered_development_levels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("level_name", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # 将 is_revitalization_tier 数据迁移回 revitalization_tier
    op.execute(
        "UPDATE supported_villages SET revitalization_tier = '是' "
        "WHERE is_revitalization_tier = 1"
    )

    # 删除 is_revitalization_tier 列
    with op.batch_alter_table("supported_villages") as batch_op:
        batch_op.drop_column("is_revitalization_tier")

    # 重建索引
    op.create_index("ix_supported_villages_tier", "supported_villages", ["revitalization_tier"], if_not_exists=True)
    op.create_index("ix_villages_province_tier", "supported_villages", ["province", "revitalization_tier"], if_not_exists=True)
    op.create_index("ix_villages_county_tier", "supported_villages", ["county", "revitalization_tier"], if_not_exists=True)
