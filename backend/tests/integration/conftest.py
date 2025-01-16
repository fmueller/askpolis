import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("pgvector/pgvector:pg17") as container:
        yield container.start()


@pytest.fixture(scope="session")
def alembic_config():
    config = Config("src/alembic.ini")
    config.set_main_option("script_location", "src/alembic")
    return config


@pytest.fixture(scope="session")
def test_db_url(postgres_container):
    return postgres_container.get_connection_url().replace("psycopg2", "psycopg")


@pytest.fixture(scope="function")
def database(postgres_container, alembic_config, test_db_url):
    alembic_config.set_main_option("sqlalchemy.url", test_db_url)
    command.upgrade(alembic_config, "head")
    yield create_engine(test_db_url)
    command.downgrade(alembic_config, "base")
