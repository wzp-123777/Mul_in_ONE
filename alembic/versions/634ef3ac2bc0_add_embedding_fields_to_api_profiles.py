"""add_embedding_fields_to_api_profiles

Revision ID: 634ef3ac2bc0
Revises: e23b22c205c4
Create Date: 2025-11-29 18:33:31.592849

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '634ef3ac2bc0'
down_revision = 'e23b22c205c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_embedding_model column (defaults to False for existing profiles)
    op.add_column('api_profiles', sa.Column('is_embedding_model', sa.Boolean(), nullable=False, server_default='false'))
    # Add embedding_dim column - stores the MAXIMUM dimension supported by the model
    # (e.g., 4096 for Qwen3-Embedding-8B, 1536 for OpenAI text-embedding-3-small)
    # Users can specify smaller dimensions at runtime (e.g., 32-4096) to save storage
    op.add_column('api_profiles', sa.Column('embedding_dim', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('api_profiles', 'embedding_dim')
    op.drop_column('api_profiles', 'is_embedding_model')
