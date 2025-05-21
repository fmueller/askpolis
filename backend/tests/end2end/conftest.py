import re
import subprocess
import threading
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import requests
import yaml
from docker import from_env
from docker.models.networks import Network
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from askpolis.logging import configure_logging, get_logger

configure_logging()

containers_logger = get_logger("containers")

# Name of the very small LLM to use for tests
ollama_model = "qwen2:0.5b"


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


def _get_service_image_version_from_compose(service_name: str) -> str:
    compose_path = Path(__file__).parent.parent.parent / "compose.yaml"
    with compose_path.open() as f:
        data = yaml.safe_load(f)
    services = data.get("services", {})
    service = services.get(service_name)
    if not service:
        raise RuntimeError(f"Service '{service_name}' not found in compose.yaml")
    image = service.get("image", "")
    if ":" not in image:
        raise RuntimeError(f"No version tag found for '{service_name}' in compose.yaml")
    return image.split(":", 1)[1]


def _get_ollama_version_from_dockerfile() -> str:
    dockerfile_path = Path(__file__).parent.parent.parent / "ollama.Dockerfile"
    version_pattern = re.compile(r"^FROM\s+ollama/ollama:([^\s]+)")
    with dockerfile_path.open() as f:
        for line in f:
            match = version_pattern.match(line)
            if match:
                return match.group(1)
    raise RuntimeError("Could not find Ollama version in ollama.Dockerfile")


@pytest.fixture(scope="session")
def docker_network() -> Generator[Network, None, None]:
    client = from_env()
    network = client.networks.create(name="askpolis_e2e_test_shared", driver="bridge", check_duplicate=True)
    yield network
    network.remove()


@pytest.fixture(scope="session")
def ollama_container(docker_network: Network) -> Generator[DockerContainer, None, None]:
    with (
        DockerContainer(f"ollama/ollama:{_get_ollama_version_from_dockerfile()}")
        .with_network(docker_network)
        .with_network_aliases("ollama")
        .with_exposed_ports(11434) as container
    ):
        _attach_log_stream(container, "[ollama] ")

        host = container.get_container_host_ip()
        port = container.get_exposed_port(11434)
        base_url = f"http://{host}:{port}"

        for _ in range(60):
            try:
                resp = requests.get(f"{base_url}/api/tags", timeout=2)
                if resp.status_code == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            pytest.fail("Ollama container did not start within the expected time.")

        # Pull the LLM model via Ollama's API
        resp = requests.post(
            f"{base_url}/api/pull",
            json={"name": ollama_model},
            timeout=5,
        )
        if resp.status_code != 200:
            pytest.fail(f"Failed to initiate LLM pull from Ollama: {resp.status_code} {resp.text}")

        # Wait for the model to appear in /api/tags
        for _ in range(60):
            tags = requests.get(f"{base_url}/api/tags", timeout=2).json()
            model_names = [tag.get("name") for tag in tags.get("models", [])]
            if ollama_model in model_names:
                break
            time.sleep(2)
        else:
            pytest.fail(f"Ollama model '{ollama_model}' was not pulled successfully.")

        yield container


@pytest.fixture(scope="session")
def ollama_url(ollama_container: DockerContainer) -> str:
    return "http://ollama:11434/v1"


@pytest.fixture(scope="session")
def redis_container(docker_network: Network) -> Generator[RedisContainer, None, None]:
    with (
        RedisContainer(f"redis:{_get_service_image_version_from_compose('redis')}")
        .with_network(docker_network)
        .with_network_aliases("redis") as container
    ):
        _attach_log_stream(container, "[redis] ")
        yield container


@pytest.fixture(scope="session")
def celery_broker_url(redis_container: RedisContainer) -> str:
    return "redis://redis:6379/0"


@pytest.fixture(scope="session")
def postgres_container(docker_network: Network) -> Generator[PostgresContainer, Any, None]:
    postgres_version = _get_service_image_version_from_compose("postgres")
    with (
        PostgresContainer(image=f"pgvector/pgvector:{postgres_version}", driver="psycopg")
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
    docker_test_image: str,
    docker_network: Network,
    test_db_connection_url: str,
    celery_broker_url: str,
    ollama_url: str,
) -> Generator[DockerContainer, None, None]:
    with (
        DockerContainer(docker_test_image)
        .with_network(docker_network)
        .with_env("CELERY_BROKER_URL", celery_broker_url)
        .with_env("DATABASE_URL", test_db_connection_url)
        .with_env("OLLAMA_URL", ollama_url)
        .with_env("OLLAMA_MODEL", ollama_model)
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
    ollama_url: str,
) -> Generator[str, None, None]:
    with (
        DockerContainer(docker_test_image)
        .with_network(docker_network)
        .with_env("CELERY_BROKER_URL", celery_broker_url)
        .with_env("DATABASE_URL", test_db_connection_url)
        .with_env("OLLAMA_URL", ollama_url)
        .with_env("OLLAMA_MODEL", ollama_model)
        .with_env("DISABLE_INFERENCE", "true")
        .with_exposed_ports(8000)
        .with_command("./scripts/start-api.sh") as container
    ):
        _attach_log_stream(container, "[api] ")
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8000)
        base_url = f"http://{host}:{port}"

        for _ in range(60):
            try:
                response = requests.get(base_url, timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            pytest.fail("The API did not start within the expected time.")

        yield base_url
