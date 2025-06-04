import os
import threading
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml
from docker.models.networks import Network
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config
from askpolis.logging import get_logger

containers_logger = get_logger("containers")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        test_path = os.path.abspath(item.location[0]).replace("\\", "/")

        if "tests/unit" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "tests/integration" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "tests/end2end" in test_path:
            item.add_marker(pytest.mark.e2e)


def attach_log_stream(container: DockerContainer, prefix: str) -> None:
    """
    Spins up a daemon thread that tails container logs and emits to logger.
    """

    def _stream() -> None:
        for raw_line in container.get_wrapped_container().logs(stream=True, follow=True):
            try:
                text = raw_line.decode(encoding="utf-8", errors="ignore").rstrip()
            except Exception:
                text = repr(raw_line)
            containers_logger.info(f"{prefix}{text}")

    thread = threading.Thread(target=_stream, daemon=True, name=f"log-stream-{prefix}")
    thread.start()


def get_service_image_version_from_compose(service_name: str) -> str:
    compose_path = Path(__file__).parent.parent / "compose.yaml"
    with compose_path.open() as f:
        data = yaml.safe_load(f)
    services = data.get("services", {})
    service = services.get(service_name)
    if not service:
        raise RuntimeError(f"Service '{service_name}' not found in compose.yaml")
    image = service.get("image", "")
    if ":" not in image:
        raise RuntimeError(f"No version tag found for '{service_name}' in compose.yaml")
    return str(image.split(":", 1)[1])


class PostgresTestBase:
    """Base class for PostgreSQL test fixtures"""

    @staticmethod
    def create_postgres_container(
        version: str | None = None, network: Network | None = None, with_logging: bool = True
    ) -> PostgresContainer:
        if version is None:
            version = get_service_image_version_from_compose("postgres")

        container = PostgresContainer(image=f"pgvector/pgvector:{version}", driver="psycopg")

        if network:
            container = container.with_network(network).with_network_aliases("postgres")

        if with_logging:
            attach_log_stream(container, "[postgres] ")

        return container

    @staticmethod
    def get_alembic_config() -> Config:
        config = Config(Path(__file__).parent.parent / "src/alembic.ini")
        config.set_main_option("script_location", (Path(__file__).parent.parent / "src/alembic").absolute().as_posix())
        return config

    @staticmethod
    def setup_database_with_migrations(connection_url: str) -> Engine:
        alembic_config = PostgresTestBase.get_alembic_config()
        alembic_config.set_main_option("sqlalchemy.url", connection_url)
        command.upgrade(alembic_config, "head")
        return create_engine(connection_url)

    @staticmethod
    def cleanup_database(connection_url: str) -> None:
        alembic_config = PostgresTestBase.get_alembic_config()
        alembic_config.set_main_option("sqlalchemy.url", connection_url)
        command.downgrade(alembic_config, "base")


def create_transactional_session(session_maker: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Create a database session with automatic rollback for test isolation."""
    connection = session_maker.kw["bind"].connect()
    transaction = connection.begin()
    session = session_maker(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
