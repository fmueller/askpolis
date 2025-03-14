"""add_embeddings_tables

Revision ID: 6dcdadab04b6
Revises: 79cf11662b6f
Create Date: 2025-03-14 14:22:09.285567

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6dcdadab04b6"
down_revision: Union[str, None] = "79cf11662b6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "embeddings_collections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("page_id", sa.UUID(), nullable=False),
        sa.Column("chunk", sa.String(), nullable=False),
        sa.Column("embedding", VECTOR(1024), nullable=False),
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
    op.drop_table("embeddings")
    op.drop_table("embeddings_collections")
