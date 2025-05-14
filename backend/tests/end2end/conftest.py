import subprocess
import threading
import time
from collections.abc import Generator
from typing import Any

import pytest
import requests
from docker import from_env
from docker.models.networks import Network
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from askpolis.logging import configure_logging, get_logger

configure_logging()

containers_logger = get_logger("containers")


def _attach_log_stream(container: DockerContainer, prefix: str) -> None:
    """
    Spins up a daemon thread that tails `container.logs(stream=True, follow=True)`
    and emits each line to our `containers` logger.
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


@pytest.fixture(scope="session")
def docker_network() -> Generator[Network, None, None]:
    client = from_env()
    network = client.networks.create(name="askpolis_e2e_test_shared", driver="bridge", check_duplicate=True)
    yield network
    network.remove()


@pytest.fixture(scope="session")
def redis_container(docker_network: Network) -> Generator[RedisContainer, None, None]:
    with RedisContainer("redis:7.4.2-bookworm").with_network(docker_network).with_network_aliases("redis") as container:
        _attach_log_stream(container, "[redis] ")
        yield container


@pytest.fixture(scope="session")
def celery_broker_url(redis_container: RedisContainer) -> str:
    return "redis://redis:6379/0"


@pytest.fixture(scope="session")
def postgres_container(docker_network: Network) -> Generator[PostgresContainer, Any, None]:
    with (
        PostgresContainer(image="pgvector/pgvector:pg17", driver="psycopg")
        .with_network(docker_network)
        .with_network_aliases("postgres") as container
    ):
        _attach_log_stream(container, "[postgres] ")
        yield container


@pytest.fixture(scope="session")
def test_db_connection_url(postgres_container: PostgresContainer) -> str:
    return f"postgresql+psycopg://{postgres_container.username}:{postgres_container.password}@postgres:5432/{postgres_container.dbname}"


@pytest.fixture(scope="session")
def docker_test_image() -> str:
    """
    Build the Docker image with a build argument to disable Hugging Face downloads
    """
    result = subprocess.run(
        [
            "docker",
            "build",
            "--build-arg",
            "DISABLE_HUGGINGFACE_DOWNLOAD=true",
            "--target",
            "runtime",
            "-t",
            "askpolis-e2e-test",
            "-f",
            "Dockerfile",
            ".",
        ],
        check=True,
    )
    assert result.returncode == 0
    return "askpolis-e2e-test:latest"


@pytest.fixture(scope="session")
def worker_container(
    docker_test_image: str, docker_network: Network, test_db_connection_url: str, celery_broker_url: str
) -> Generator[DockerContainer, None, None]:
    with (
        DockerContainer(docker_test_image)
        .with_network(docker_network)
        .with_env("CELERY_BROKER_URL", celery_broker_url)
        .with_env("DATABASE_URL", test_db_connection_url)
        .with_env("DISABLE_INFERENCE", "true")
        .with_command("./scripts/start-worker.sh") as container
    ):
        _attach_log_stream(container, "[worker] ")
        yield container


@pytest.fixture(scope="session")
def api_url(
    docker_test_image: str,
    docker_network: Network,
    worker_container: DockerContainer,
    test_db_connection_url: str,
    celery_broker_url: str,
) -> Generator[str, None, None]:
    with (
        DockerContainer(docker_test_image)
        .with_network(docker_network)
        .with_env("CELERY_BROKER_URL", celery_broker_url)
        .with_env("DATABASE_URL", test_db_connection_url)
        .with_env("DISABLE_INFERENCE", "true")
        .with_exposed_ports(8000)
        .with_command("./scripts/start-api.sh") as container
    ):
        _attach_log_stream(container, "[api] ")
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8000)
        base_url = f"http://{host}:{port}"

        for _ in range(30):
            try:
                response = requests.get(base_url, timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            pytest.fail("The API did not start within the expected time.")

        yield base_url
