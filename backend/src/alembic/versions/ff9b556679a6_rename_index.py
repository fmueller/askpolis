"""rename_index

Revision ID: ff9b556679a6
Revises: 0bc41aaee68f
Create Date: 2025-01-31 14:04:41.178626

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ff9b556679a6"
down_revision: str | None = "0bc41aaee68f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER INDEX crawling_results_pkey RENAME TO fetched_data_pkey")


def downgrade() -> None:
    op.execute("ALTER INDEX fetched_data_pkey RENAME TO crawling_results_pkey")
