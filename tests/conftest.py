"""Test fixtures."""

import re
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from typing import Any, NamedTuple

import pytest
from build.publish import main
from build.utils import create_tag, get_image_reference
from click.testing import CliRunner, Result
from python_on_whales import DockerClient
from testcontainers.registry import DockerRegistryContainer

from tests.constants import REGISTRY_TOKEN, REGISTRY_USERNAME


class PublishedImage(NamedTuple):
    """References of the container image published to the local test registry."""

    registry: str
    tag: str
    image_reference_latest: str


@pytest.fixture(scope="function")
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
        yield tmp_server_description_path


@pytest.fixture(scope="session")
def podman_client() -> DockerClient:
    """Provide the Python on Whales client configured for Podman.

    :return:
    """
    return DockerClient(client_call=["podman"], client_type="podman", debug=True)


@pytest.fixture(scope="session")
def registry_container() -> Generator[DockerRegistryContainer, Any]:
    """Provide a Registry container locally for publishing the image.

    :return:
    """
    with DockerRegistryContainer().with_bind_ports(5000, 5000) as registry_container:
        yield registry_container


@pytest.fixture(scope="session")
def published_image(
    registry_container: DockerRegistryContainer,
    cli_runner: CliRunner,
) -> PublishedImage:
    """Build the container image once and publish it to the local test registry.

    Building the image is slow (steamcmd downloads the game server inside the
    build), so the build runs once per test session and all slow tests share
    the resulting image.

    :param registry_container:
    :param cli_runner:
    :return:
    """
    result: Result = cli_runner.invoke(
        main,
        env={
            "DOCKER_HUB_USERNAME": REGISTRY_USERNAME,
            "DOCKER_HUB_TOKEN": REGISTRY_TOKEN,
            "REGISTRY": registry_container.get_registry(),
            "PUBLISH_MANUALLY": "1",
        },
    )
    assert result.exit_code == 0, result.output

    # The publish CLI already queried Steam for the current build id, so it is
    # reused from the CLI output instead of a second Steam round trip.
    match: re.Match[str] | None = re.search(
        r"Current Windrose server build ID: (\S+)", result.output
    )
    assert match is not None, result.output

    registry: str = registry_container.get_registry()
    return PublishedImage(
        registry=registry,
        tag=create_tag(match.group(1)),
        image_reference_latest=get_image_reference(registry, "latest"),
    )


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    """Provide CLI runner for testing click CLI.

    :return:
    """
    runner = CliRunner()
    return runner
