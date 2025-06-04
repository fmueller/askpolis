"""add_unique_index_on_document_refs

Revision ID: a1b2c3d4e5f6
Revises: 115433b912f3
Create Date: 2025-05-23 17:30:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "115433b912f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_documents_ref1_ref2_unique",
        "documents",
        ["reference_id_1", "reference_id_2"],
        unique=True,
        postgresql_where=sa.text("reference_id_1 IS NOT NULL AND reference_id_2 IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_documents_ref1_ref2_unique", table_name="documents")
