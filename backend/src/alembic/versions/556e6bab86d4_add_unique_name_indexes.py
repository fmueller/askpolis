"""add_unique_name_indexes

Revision ID: 556e6bab86d4
Revises: 323cf93d21fb
Create Date: 2025-07-10 08:41:29.338609

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "556e6bab86d4"
down_revision: Union[str, None] = "323cf93d21fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("uq_parliaments_name", "parliaments", ["name"], unique=True)
    op.create_index("uq_parties_name", "parties", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_parties_name", table_name="parties")
    op.drop_index("uq_parliaments_name", table_name="parliaments")
