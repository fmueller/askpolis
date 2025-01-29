"""rename_crawling_results_table

Revision ID: 0bc41aaee68f
Revises: b7b091f333f9
Create Date: 2025-01-29 13:00:52.966250

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0bc41aaee68f"
down_revision: Union[str, None] = "b7b091f333f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("crawling_results", "fetched_data")
    op.alter_column("fetched_data", "crawler", new_column_name="data_fetcher")


def downgrade() -> None:
    op.alter_column("fetched_data", "data_fetcher", new_column_name="crawler")
    op.rename_table("fetched_data", "crawling_results")
