"""add_sparse_embeddings_column

Revision ID: fe993b39c6fd
Revises: 4ee6341a2884
Create Date: 2025-03-20 12:25:21.733492

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from pgvector.sqlalchemy.sparsevec import SPARSEVEC
from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fe993b39c6fd"
down_revision: Union[str, None] = "4ee6341a2884"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("embeddings", if_exists=True)
    op.create_table(
        "embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("page_id", sa.UUID(), nullable=False),
        sa.Column("chunk", sa.String(), nullable=False),
        sa.Column("embedding", VECTOR(1024), nullable=False),
        sa.Column("sparse_embedding", SPARSEVEC(250002), nullable=False),
        sa.Column("chunk_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now(timezone=True)),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["embeddings_collections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("embeddings", if_exists=True)
