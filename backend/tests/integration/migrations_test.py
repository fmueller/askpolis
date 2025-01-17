from collections.abc import Generator

from sqlalchemy import Engine

from alembic import command
from alembic.config import Config


# TODO add test for ollama docker image
def test_migration_stairway(database: Generator[Engine], alembic_config: Config) -> None:
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
