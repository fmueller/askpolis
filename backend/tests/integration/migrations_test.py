from alembic.config import Config

from alembic import command


def test_migration_stairway(alembic_config: Config) -> None:
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
