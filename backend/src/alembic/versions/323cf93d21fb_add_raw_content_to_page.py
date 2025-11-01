"""add_raw_content_to_page

Revision ID: 323cf93d21fb
Revises: c2a2dd9f9ec7
Create Date: 2025-07-08 12:20:03.877640

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "323cf93d21fb"
down_revision: str | None = "c2a2dd9f9ec7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pages", sa.Column("raw_content", sa.Text(), nullable=False, server_default="no content"))
    pass


def downgrade() -> None:
    op.drop_column("pages", "raw_content")
    pass
