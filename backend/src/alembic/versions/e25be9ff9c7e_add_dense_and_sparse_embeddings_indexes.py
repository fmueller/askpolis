"""add_dense_and_sparse_embeddings_indexes

Revision ID: e25be9ff9c7e
Revises: fe993b39c6fd
Create Date: 2025-03-20 20:02:24.736747

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e25be9ff9c7e"
down_revision: str | None = "fe993b39c6fd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "hnsw_cosine_dense_idx",
            "embeddings",
            [sa.text("embedding vector_cosine_ops")],
            postgresql_using="hnsw",
            postgresql_with={"m": 24, "ef_construction": 128},
            postgresql_concurrently=True,
        )
        op.create_index(
            "hnsw_cosine_sparse_idx",
            "embeddings",
            [sa.text("sparse_embedding sparsevec_cosine_ops")],
            postgresql_using="hnsw",
            postgresql_with={"m": 24, "ef_construction": 128},
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("hnsw_cosine_sparse_idx", table_name="embeddings", postgresql_concurrently=True, if_exists=True)
        op.drop_index("hnsw_cosine_dense_idx", table_name="embeddings", postgresql_concurrently=True, if_exists=True)
