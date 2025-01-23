from collections.abc import Generator
from typing import cast

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.core.generic import DbContainer
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config


@pytest.fixture(scope="session")
def postgres_container() -> DbContainer:
    with PostgresContainer("pgvector/pgvector:pg17") as container:
        yield container.start()


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    config = Config("src/alembic.ini")
    config.set_main_option("script_location", "src/alembic")
    return config


@pytest.fixture(scope="session")
def test_db_url(postgres_container: DbContainer) -> str:
    return cast(str, postgres_container.get_connection_url().replace("psycopg2", "psycopg"))


@pytest.fixture(scope="function")
def database(postgres_container: DbContainer, alembic_config: Config, test_db_url: str) -> Generator[Engine]:
    alembic_config.set_main_option("sqlalchemy.url", test_db_url)
    command.upgrade(alembic_config, "head")
    yield create_engine(test_db_url)
    command.downgrade(alembic_config, "base")


@pytest.fixture(scope="function")
def session_maker(database: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=database)
