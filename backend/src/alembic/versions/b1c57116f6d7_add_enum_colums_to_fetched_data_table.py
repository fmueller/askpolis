"""add_enum_colums_to_fetched_data_table

Revision ID: b1c57116f6d7
Revises: 489b0743314c
Create Date: 2025-02-03 13:37:33.824641

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

from alembic import op
from askpolis.data_fetcher import DataFetcherType, EntityType

# revision identifiers, used by Alembic.
revision: str = "b1c57116f6d7"
down_revision: Union[str, None] = "489b0743314c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    data_fetcher_enum_type = postgresql.ENUM(*DataFetcherType.values(), name="datafetchertype")
    data_fetcher_enum_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "fetched_data",
        sa.Column(
            "data_fetcher_type",
            data_fetcher_enum_type,
            nullable=False,
            server_default=DataFetcherType.ABGEORDNETENWATCH.value,
        ),
    )

    entity_type_enum_type = postgresql.ENUM(*EntityType.values(), name="entitytypetype")
    entity_type_enum_type.create(op.get_bind(), checkfirst=True)
    op.add_column("fetched_data", sa.Column("entity_type", entity_type_enum_type, nullable=True))
    op.add_column("fetched_data", sa.Column("is_list", sa.Boolean(), nullable=False, server_default="false"))

    op.alter_column(
        "fetched_data", "created_at", server_default=func.now(timezone=True), existing_type=sa.DateTime(timezone=True)
    )

    fetched_data_table = sa.sql.table("fetched_data", sa.Column("created_at", sa.DateTime(timezone=True)))
    op.execute(
        fetched_data_table.update()
        .where(fetched_data_table.c.created_at.is_(None))
        .values(created_at=func.now(timezone=True))
    )

    op.alter_column("fetched_data", "created_at", nullable=False, existing_type=sa.DateTime(timezone=True))


def downgrade() -> None:
    op.alter_column(
        "fetched_data", "created_at", nullable=True, server_default=None, existing_type=sa.DateTime(timezone=True)
    )
    op.drop_column("fetched_data", "is_list")
    op.drop_column("fetched_data", "entity_type")
    postgresql.ENUM(name="entitytypetype").drop(op.get_bind(), checkfirst=True)
    op.drop_column("fetched_data", "data_fetcher_type")
    postgresql.ENUM(name="datafetchertype").drop(op.get_bind(), checkfirst=True)
