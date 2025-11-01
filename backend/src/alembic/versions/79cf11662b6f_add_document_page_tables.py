"""add_document_page_tables

Revision ID: 79cf11662b6f
Revises: ff3d5ee26d03
Create Date: 2025-03-11 18:49:28.185203

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

from alembic import op
from askpolis.core import DocumentType

# revision identifiers, used by Alembic.
revision: str = "79cf11662b6f"
down_revision: str | None = "ff3d5ee26d03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    document_type_enum_type = postgresql.ENUM(*DocumentType.values(), name="documenttypetype")
    document_type_enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("reference_id_1", sa.UUID(), nullable=True),
        sa.Column("reference_id_2", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("documents", sa.Column("document_type", document_type_enum_type, nullable=False))
    op.create_table(
        "pages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("page_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now(timezone=True)),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pages")
    op.drop_table("documents")
    postgresql.ENUM(name="documenttypetype").drop(op.get_bind(), checkfirst=True)
