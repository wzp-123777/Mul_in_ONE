"""add fastapi users auth tables

Revision ID: 20251202_0004
Revises: 20251201_0003
Create Date: 2025-12-02 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251202_0004'
down_revision = '20251201_0003'
branch_labels = None
depends_on = None


def upgrade():
    # 修改 users 表以兼容 FastAPI-Users
    with op.batch_alter_table('users') as batch_op:
        # 重命名 password_hash 为 hashed_password
        batch_op.alter_column('password_hash', 
                            new_column_name='hashed_password',
                            existing_type=sa.String(length=255),
                            type_=sa.String(length=1024),
                            nullable=True)
        
        # 添加 FastAPI-Users 必需字段
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'))
        
        # 确保 email 字段有唯一索引
        batch_op.create_index('ix_users_email', ['email'], unique=True)
        
        # 确保 username 字段有索引
        batch_op.create_index('ix_users_username', ['username'], unique=True)
    
    # 创建 OAuth 账户表
    op.create_table(
        'oauth_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('oauth_name', sa.String(length=100), nullable=False),
        sa.Column('access_token', sa.String(length=1024), nullable=False),
        sa.Column('expires_at', sa.Integer(), nullable=True),
        sa.Column('refresh_token', sa.String(length=1024), nullable=True),
        sa.Column('account_id', sa.String(length=320), nullable=False),
        sa.Column('account_email', sa.String(length=320), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('oauth_accounts') as batch_op:
        batch_op.create_index('ix_oauth_accounts_account_id', ['account_id'])
        batch_op.create_index('ix_oauth_accounts_oauth_name', ['oauth_name'])


def downgrade():
    # 删除 OAuth 表
    op.drop_table('oauth_accounts')
    
    # 恢复 users 表
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_username')
        batch_op.drop_index('ix_users_email')
        batch_op.drop_column('is_verified')
        batch_op.drop_column('is_superuser')
        batch_op.drop_column('is_active')
        
        # 恢复原始字段名
        batch_op.alter_column('hashed_password',
                            new_column_name='password_hash',
                            existing_type=sa.String(length=1024),
                            type_=sa.String(length=255),
                            nullable=True)
