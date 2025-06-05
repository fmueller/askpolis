"""add_chunk_id_column_to_embeddings

Revision ID: d4ccab584cc8
Revises: eaf0c2631dbf
Create Date: 2025-06-05 09:16:40.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4ccab584cc8"
down_revision: Union[str, None] = "eaf0c2631dbf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("embeddings", sa.Column("chunk_id", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("embeddings", "chunk_id", server_default=None)


def downgrade() -> None:
    op.drop_column("embeddings", "chunk_id")
