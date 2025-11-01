"""add_vector_index

Revision ID: 4ee6341a2884
Revises: 6dcdadab04b6
Create Date: 2025-03-17 19:27:58.241753

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ee6341a2884"
down_revision: str | None = "6dcdadab04b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "hnsw_cosine_idx",
            "embeddings",
            [sa.text("embedding vector_cosine_ops")],
            postgresql_using="hnsw",
            postgresql_with={"m": 24, "ef_construction": 128},
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("hnsw_cosine_idx", table_name="embeddings", postgresql_concurrently=True, if_exists=True)
