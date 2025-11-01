"""add_citations_table

Revision ID: 115433b912f3
Revises: eaf0c2631dbf
Create Date: 2025-05-16 11:50:17.696085

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "115433b912f3"
down_revision: str | None = "eaf0c2631dbf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "citations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer_id", sa.UUID(), nullable=False),
        sa.Column("embeddings_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("page_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["embeddings_id"],
            ["embeddings.id"],
        ),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("answer_id", "embeddings_id", "document_id", "page_id", name="uq_citations_dims"),
    )


def downgrade() -> None:
    op.drop_table("citations")
