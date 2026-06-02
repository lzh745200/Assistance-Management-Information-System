"""add encryption fields to data_packages

Revision ID: 007_add_encryption_fields
Revises: 006_add_effectiveness_sentiment_tables
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """添加加密相关字段到data_packages表"""
    op.add_column('data_packages',
        sa.Column('is_encrypted', sa.Boolean(), default=False, nullable=True, comment='是否加密'))
    op.add_column('data_packages',
        sa.Column('encryption_algorithm', sa.String(50), nullable=True, comment='加密算法'))
    op.add_column('data_packages',
        sa.Column('encryption_salt', sa.String(128), nullable=True, comment='密钥派生盐值(hex)'))
    op.add_column('data_packages',
        sa.Column('encryption_iterations', sa.Integer(), nullable=True, comment='PBKDF2迭代次数'))


def downgrade():
    """移除加密相关字段"""
    op.drop_column('data_packages', 'encryption_iterations')
    op.drop_column('data_packages', 'encryption_salt')
    op.drop_column('data_packages', 'encryption_algorithm')
    op.drop_column('data_packages', 'is_encrypted')
