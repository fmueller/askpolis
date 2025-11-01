"""add_crawling_results_table

Revision ID: 77216f666286
Revises: 147619a67ee1
Create Date: 2025-01-19 17:45:26.561453

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "77216f666286"
down_revision: str | None = "147619a67ee1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crawling_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("crawler", sa.String(), nullable=False),
        sa.Column("entity", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("text_data", sa.String(), nullable=True),
        sa.Column("json_data", JSONB, nullable=True),
        sa.Column("file_data", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("crawling_results")
