"""remove_langchain_tables

Revision ID: 1b3e1b887c35
Revises: ff9b556679a6
Create Date: 2025-01-31 16:19:22.918960

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b3e1b887c35"
down_revision: Union[str, None] = "ff9b556679a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("langchain_pg_embedding", if_exists=True)
    op.drop_table("langchain_pg_collection", if_exists=True)
    pass


def downgrade() -> None:
    # we don't support downgrades for this migration
    # because we don't want to use the langchain-postgres library anymore
    pass
