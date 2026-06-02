"""添加机器码管理表

Revision ID: 009
Revises: 008
Create Date: 2026-03-15 15:16:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    """创建机器码管理表"""
    op.create_table(
        'machine_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('machine_code', sa.String(length=255), nullable=False, comment='机器码（基于硬件信息生成）'),
        sa.Column('pass_code', sa.String(length=255), nullable=False, comment='通行码（激活码）'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态: pending-待使用, active-已激活, revoked-已撤销'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='绑定的用户ID'),
        sa.Column('description', sa.Text(), nullable=True, comment='备注说明'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID（管理员）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True, comment='创建时间'),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True, comment='激活时间'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True, comment='撤销时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_machine_codes_machine_code', 'machine_codes', ['machine_code'], unique=True)
    op.create_index('ix_machine_codes_pass_code', 'machine_codes', ['pass_code'], unique=True)
    op.create_index('ix_machine_codes_status', 'machine_codes', ['status'], unique=False)
    op.create_index('ix_machine_codes_user_id', 'machine_codes', ['user_id'], unique=False)


def downgrade():
    """删除机器码管理表"""
    op.drop_index('ix_machine_codes_user_id', table_name='machine_codes')
    op.drop_index('ix_machine_codes_status', table_name='machine_codes')
    op.drop_index('ix_machine_codes_pass_code', table_name='machine_codes')
    op.drop_index('ix_machine_codes_machine_code', table_name='machine_codes')
    op.drop_table('machine_codes')
