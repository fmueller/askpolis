"""add_chunk_id_column_to_embeddings

Revision ID: c2a2dd9f9ec7
Revises: a1b2c3d4e5f6
Create Date: 2025-06-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c2a2dd9f9ec7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("embeddings", sa.Column("chunk_id", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("embeddings", "chunk_id", server_default=None)


def downgrade() -> None:
    op.drop_column("embeddings", "chunk_id")
