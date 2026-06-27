"""添加安全增强相关表

Revision ID: 004
Revises: 003
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """添加安全增强相关表"""

    # 双因素认证表
    op.create_table(
        'two_factor_auth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('secret_key', sa.String(length=255), nullable=False),
        sa.Column('backup_codes', sa.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_two_factor_auth_user_id', 'two_factor_auth', ['user_id'])

    # 审计变更记录表
    op.create_table(
        'audit_changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audit_log_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('change_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['audit_log_id'], ['audit_logs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_changes_audit_log_id', 'audit_changes', ['audit_log_id'])
    op.create_index('idx_audit_changes_field_name', 'audit_changes', ['field_name'])


def downgrade():
    """移除安全增强相关表"""

    op.drop_index('idx_audit_changes_field_name', table_name='audit_changes')
    op.drop_index('idx_audit_changes_audit_log_id', table_name='audit_changes')
    op.drop_table('audit_changes')

    op.drop_index('idx_two_factor_auth_user_id', table_name='two_factor_auth')
    op.drop_table('two_factor_auth')
