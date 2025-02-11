"""add_updated_at_to_core_models

Revision ID: ff3d5ee26d03
Revises: b1c57116f6d7
Create Date: 2025-02-11 12:52:33.700171

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy import func

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ff3d5ee26d03"
down_revision: Union[str, None] = "b1c57116f6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("election_programs", "last_updated_at", new_column_name="updated_at")
    op.alter_column(
        "election_programs",
        "updated_at",
        server_default=func.now(timezone=True),
        existing_type=sa.DateTime(timezone=True),
    )

    election_programs_table = sa.sql.table("election_programs", sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.execute(
        election_programs_table.update()
        .where(election_programs_table.c.updated_at.is_(None))
        .values(updated_at=func.now(timezone=True))
    )

    op.alter_column("election_programs", "updated_at", nullable=False, existing_type=sa.DateTime(timezone=True))

    op.add_column(
        "parliament_periods",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now(timezone=True)),
    )
    op.add_column(
        "parliaments",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now(timezone=True)),
    )
    op.add_column(
        "parties",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now(timezone=True)),
    )


def downgrade() -> None:
    op.drop_column("parties", "updated_at")
    op.drop_column("parliaments", "updated_at")
    op.drop_column("parliament_periods", "updated_at")
    op.alter_column(
        "election_programs", "updated_at", nullable=True, server_default=None, existing_type=sa.DateTime(timezone=True)
    )
    op.alter_column("election_programs", "updated_at", new_column_name="last_updated_at")
