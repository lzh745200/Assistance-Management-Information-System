"""baseline: 标记当前数据库 schema 为初始基线

Revision ID: 001
Revises: None
Create Date: 2026-02-14

说明：
    这是初始基线迁移。现有数据库表已通过 create_all + _migrate_missing_columns 创建。
    此脚本仅作为 Alembic 迁移历史的起点，不执行任何 DDL 操作。
    后续新的 schema 变更应通过 `alembic revision --autogenerate -m "描述"` 生成。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 基线迁移，现有表已存在，无需操作
    pass


def downgrade() -> None:
    # 基线迁移不支持降级
    pass
