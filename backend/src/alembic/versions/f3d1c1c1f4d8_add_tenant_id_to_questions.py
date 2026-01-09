"""add tenant id to questions

Revision ID: f3d1c1c1f4d8
Revises: eaf0c2631dbf
Create Date: 2025-05-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3d1c1c1f4d8"
down_revision: str | None = "eaf0c2631dbf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column(
            "tenant_id",
            sa.UUID(),
            nullable=False,
            server_default="00000000-0000-0000-0000-000000000000",
        ),
    )
    op.alter_column("questions", "tenant_id", server_default=None)
    op.create_index("idx_questions_tenant_id", "questions", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("idx_questions_tenant_id", table_name="questions")
    op.drop_column("questions", "tenant_id")
