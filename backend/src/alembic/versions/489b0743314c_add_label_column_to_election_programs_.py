"""add_label_column_to_election_programs_table

Revision ID: 489b0743314c
Revises: 1b3e1b887c35
Create Date: 2025-01-31 18:41:26.308244

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "489b0743314c"
down_revision: str | None = "1b3e1b887c35"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "election_programs", sa.Column("label", sa.String(), nullable=False, server_default="default-version")
    )
    op.drop_constraint("election_programs_pkey", "election_programs", type_="primary")
    op.create_primary_key("election_programs_pkey", "election_programs", ["parliament_period_id", "party_id", "label"])
    pass


def downgrade() -> None:
    op.drop_constraint("election_programs_pkey", "election_programs", type_="primary")
    op.create_primary_key("election_programs_pkey", "election_programs", ["parliament_period_id", "party_id"])
    op.drop_column("election_programs", "label")
    pass
