"""Test fixtures."""

from collections.abc import Generator
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from click.testing import CliRunner
from python_on_whales import DockerClient
from testcontainers.registry import DockerRegistryContainer


@pytest.fixture(scope="session")
def server_description_path() -> Generator[Path, Any]:
    """Return a temporary path to a ServerDescription.json file.

    :return:
    """
    with TemporaryDirectory() as tmpdir:
        server_description_path = (
            Path(__file__).parent / "assets" / "ServerDescription.json"
        )
        tmp_server_description_path = Path(tmpdir) / "ServerDescription.json"
        copyfile(server_description_path, tmp_server_description_path)
        yield server_description_path


@pytest.fixture(scope="session")
def docker_client() -> DockerClient:
    """Provide the Python on Whales docker client.

    :return:
    """
    return DockerClient(debug=True)


@pytest.fixture(scope="session")
def registry_container() -> Generator[DockerRegistryContainer, Any]:
    """Provide a Registry container locally for publishing the image.

    :return:
    """
    with DockerRegistryContainer().with_bind_ports(5000, 5000) as registry_container:
        yield registry_container


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    """Provide CLI runner for testing click CLI.

    :return:
    """
    runner = CliRunner()
    return runner
