import subprocess
import time
from collections.abc import Generator
from typing import cast

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.core.generic import DbContainer
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container() -> DbContainer:
    with PostgresContainer("pgvector/pgvector:pg17") as container:
        yield container.start()


@pytest.fixture(scope="session")
def test_db_url(postgres_container: DbContainer) -> str:
    return cast(str, postgres_container.get_connection_url().replace("psycopg2", "psycopg"))


@pytest.fixture(scope="session")
def api_url(test_db_url: str) -> Generator[str, None, None]:
    """
    Build the Docker image with a build argument to disable Hugging Face downloads,
    then starts the Docker container using Testcontainers.
    """
    subprocess.run(
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

    with (
        DockerContainer("askpolis-e2e-test:latest")
        .with_env("CELERY_BROKER_URL", "redis://localhost:11111/0")
        .with_env("DATABASE_URL", test_db_url)
        .with_exposed_ports(8000)
        .with_command("uvicorn askpolis.main:app --host 0.0.0.0 --port 8000") as container
    ):
        # container.start()
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
