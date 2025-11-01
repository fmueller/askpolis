"""add_core_tables

Revision ID: b7b091f333f9
Revises: 77216f666286
Create Date: 2025-01-20 14:41:28.817630

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7b091f333f9"
down_revision: str | None = "77216f666286"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parliaments",
        sa.Column("id", sa.UUID, primary_key=True, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("short_name", sa.String, nullable=False),
    )
    op.create_table(
        "parties",
        sa.Column("id", sa.UUID, primary_key=True, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("short_name", sa.String, nullable=False),
    )
    op.create_table(
        "parliament_periods",
        sa.Column("id", sa.UUID, primary_key=True, nullable=False),
        sa.Column("parliament_id", sa.UUID, sa.ForeignKey("parliaments.id"), nullable=False),
        sa.Column("label", sa.String, nullable=False),
        sa.Column("period_type", sa.String, nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("election_date", sa.Date, nullable=True),
    )
    op.create_table(
        "election_programs",
        sa.Column("parliament_period_id", sa.UUID, sa.ForeignKey("parliament_periods.id"), nullable=False),
        sa.Column("party_id", sa.UUID, sa.ForeignKey("parties.id"), nullable=False),
        sa.Column("file_name", sa.String, nullable=False),
        sa.Column("file_data", sa.LargeBinary, nullable=False),
        sa.Column("last_updated_at", sa.DateTime, nullable=False),
        sa.PrimaryKeyConstraint("parliament_period_id", "party_id"),
    )


def downgrade() -> None:
    op.drop_table("election_programs")
    op.drop_table("parliament_periods")
    op.drop_table("parties")
    op.drop_table("parliaments")
