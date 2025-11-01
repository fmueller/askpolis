from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from alembic.config import Config
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.core.generic import DbContainer

from ..conftest import PostgresTestBase, create_transactional_session


@pytest.fixture(scope="session")
def postgres_container() -> Generator[DbContainer, None, None]:
    with PostgresTestBase.create_postgres_container() as container:
        yield container


@pytest.fixture(scope="session")
def alembic_config(test_db_url: str) -> Config:
    """Alembic config that uses the test database URL"""
    config = PostgresTestBase.get_alembic_config()
    config.set_main_option("sqlalchemy.url", test_db_url)
    return config


@pytest.fixture(scope="session")
def test_db_url(postgres_container: DbContainer) -> str:
    return cast(str, postgres_container.get_connection_url())


@pytest.fixture(scope="session")
def database(postgres_container: DbContainer, alembic_config: Config, test_db_url: str) -> Generator[Engine]:
    engine = PostgresTestBase.setup_database_with_migrations(test_db_url)
    yield engine
    PostgresTestBase.cleanup_database(test_db_url)


@pytest.fixture(scope="session")
def session_maker(database: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=database)


@pytest.fixture(scope="function")
def db_session(session_maker: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Provide a transactional scope around tests with automatic rollback."""
    yield from create_transactional_session(session_maker)


@pytest.fixture(scope="function")
def resources_dir() -> Path:
    return Path(__file__).parent / "resources"
