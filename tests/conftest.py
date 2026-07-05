"""Test fixtures."""

import json
import os
import re
import subprocess
import time
from collections.abc import Generator
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from typing import Any, NamedTuple
from urllib.parse import urlparse

import pytest
import requests
from build.publish import main
from build.utils import get_image_reference, get_podman_client
from click.testing import CliRunner, Result
from python_on_whales import DockerClient

from tests.constants import (
    REGISTRY_CONTAINER_NAME,
    REGISTRY_IMAGE,
    REGISTRY_PORT,
    REGISTRY_TOKEN,
    REGISTRY_USERNAME,
)

REGISTRY_READY_TIMEOUT: float = 60.0


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


def get_podman_host_architecture(podman_connection: str | None) -> str:
    """Return the architecture of a Podman connection's host.

    :param podman_connection: Podman system connection, None for the default.
    :return:
    """
    command: list[str] = ["podman"]
    if podman_connection:
        command += ["--connection", podman_connection]
    command += ["info", "--format", "{{.Host.Arch}}"]
    completed_process: subprocess.CompletedProcess[str] = subprocess.run(
        command, capture_output=True, check=True, text=True
    )
    return completed_process.stdout.strip()


def list_podman_connections() -> list[str]:
    """Return the names of all configured Podman system connections.

    :return:
    """
    completed_process: subprocess.CompletedProcess[str] = subprocess.run(
        ["podman", "system", "connection", "list", "--format", "json"],
        capture_output=True,
        check=True,
        text=True,
    )
    return [connection["Name"] for connection in json.loads(completed_process.stdout)]


@pytest.fixture(scope="session")
def podman_connection() -> str | None:
    """Resolve the Podman connection able to build the linux/amd64 image.

    The image build targets linux/amd64 and the install stage runs steamcmd,
    a 32-bit x86 binary that cannot be emulated on an arm64 Podman machine.
    If PODMAN_CONNECTION is not set and the default Podman host is not amd64,
    the first Podman system connection with an amd64 host is used instead.
    The resolved connection is exported as PODMAN_CONNECTION so the publish
    CLI and all fixtures consistently target the same Podman host.

    :return:
    """
    podman_connection: str | None = os.environ.get("PODMAN_CONNECTION")
    if podman_connection:
        return podman_connection

    default_architecture: str = get_podman_host_architecture(None)
    if default_architecture == "amd64":
        return None

    for connection in list_podman_connections():
        try:
            if get_podman_host_architecture(connection) == "amd64":
                os.environ["PODMAN_CONNECTION"] = connection
                print(
                    f"Default Podman host is {default_architecture}, using "
                    f"Podman system connection {connection} for the "
                    f"linux/amd64 image build"
                )
                return connection
        except subprocess.CalledProcessError:
            continue

    pytest.fail(
        f"The image build targets linux/amd64, but the default Podman host "
        f"is {default_architecture} and no Podman system connection with an "
        f"amd64 host was found. Set PODMAN_CONNECTION to an amd64 connection."
    )


@pytest.fixture(scope="session")
def podman_client(podman_connection: str | None) -> DockerClient:
    """Provide the Python on Whales client configured for Podman.

    Uses the same PODMAN_CONNECTION-aware client as the publish CLI, so the
    registry and test containers run on the same Podman host that builds the
    image.

    :param podman_connection:
    :return:
    """
    return get_podman_client()


def get_registry_host() -> str:
    """Return the host under which the test registry is reachable.

    Without PODMAN_CONNECTION the registry port is published on localhost
    (natively or forwarded by the local Podman machine). With a Podman system
    connection to a remote host the port is published on that host, so its
    address is resolved from the connection URI. Podman pushes to the
    registry from that host as well, so the address must be routable from
    both the test host and the Podman host.

    :return:
    """
    podman_connection: str | None = os.environ.get("PODMAN_CONNECTION")
    if not podman_connection:
        return "localhost"
    completed_process: subprocess.CompletedProcess[str] = subprocess.run(
        ["podman", "system", "connection", "list", "--format", "json"],
        capture_output=True,
        check=True,
        text=True,
    )
    for connection in json.loads(completed_process.stdout):
        if connection["Name"] == podman_connection:
            hostname: str | None = urlparse(connection["URI"]).hostname
            if hostname and hostname not in ("localhost", "127.0.0.1", "::1"):
                return hostname
    return "localhost"


@pytest.fixture(scope="session")
def registry(podman_client: DockerClient) -> Generator[str, Any]:
    """Run a registry container with Podman for publishing the image.

    The registry runs on the same Podman host that builds the image, so the
    publish CLI can push to it. Podman must trust the registry address as an
    insecure registry on the Podman host (push) and, when using a Podman
    system connection, on the local machine as well (login).

    :param podman_client:
    :return:
    """
    # A leftover registry from an aborted previous run would block the port.
    if podman_client.container.exists(REGISTRY_CONTAINER_NAME):
        podman_client.container.remove(
            REGISTRY_CONTAINER_NAME, force=True, volumes=True
        )

    podman_client.container.run(
        REGISTRY_IMAGE,
        name=REGISTRY_CONTAINER_NAME,
        publish=[(REGISTRY_PORT, REGISTRY_PORT)],
        detach=True,
    )
    registry: str = f"{get_registry_host()}:{REGISTRY_PORT}"

    deadline: float = time.monotonic() + REGISTRY_READY_TIMEOUT
    while True:
        try:
            if requests.get(f"http://{registry}/v2/", timeout=5).status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        if time.monotonic() > deadline:
            podman_client.container.remove(
                REGISTRY_CONTAINER_NAME, force=True, volumes=True
            )
            pytest.fail(
                f"Registry {registry} did not become ready within "
                f"{REGISTRY_READY_TIMEOUT} seconds"
            )
        time.sleep(1)

    yield registry

    podman_client.container.remove(REGISTRY_CONTAINER_NAME, force=True, volumes=True)


@pytest.fixture(scope="session")
def published_image(
    registry: str,
    cli_runner: CliRunner,
) -> PublishedImage:
    """Build the container image once and publish it to the local test registry.

    Building the image is slow (steamcmd downloads the game server inside the
    build), so the build runs once per test session and all slow tests share
    the resulting image.

    :param registry:
    :param cli_runner:
    :return:
    """
    result: Result = cli_runner.invoke(
        main,
        env={
            "DOCKER_HUB_USERNAME": REGISTRY_USERNAME,
            "DOCKER_HUB_TOKEN": REGISTRY_TOKEN,
            "REGISTRY": registry,
            "PUBLISH_MANUALLY": "1",
        },
    )
    assert result.exit_code == 0, result.output

    # The publish CLI already resolved the official image's build tag, so it
    # is reused from the CLI output instead of a second Docker Hub round trip.
    match: re.Match[str] | None = re.search(
        r"Current Windrose server build tag: (\S+)", result.output
    )
    assert match is not None, result.output

    return PublishedImage(
        registry=registry,
        tag=match.group(1),
        image_reference_latest=get_image_reference(registry, "latest"),
    )


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    """Provide CLI runner for testing click CLI.

    :return:
    """
    runner = CliRunner()
    return runner
