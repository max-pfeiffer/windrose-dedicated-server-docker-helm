"""Tests running a container from the built image.

The tests only wait for the configuration phase of the entrypoint (start.sh
runs update_server_description.py before it starts the game server), so they
never wait for the slow Wine/world-generation startup of the actual server.
"""

import json
import re
import time
from collections.abc import Generator
from typing import Any

import pytest
from build.scripts.update_server_description import get_game_version
from python_on_whales import Container, DockerClient

from tests.conftest import PublishedImage

pytestmark = pytest.mark.slow

SERVER_DESCRIPTION_PATH: str = "/srv/windrose/R5/ServerDescription.json"
PERSISTENT_SERVER_ID_PATH: str = "/srv/windrose/R5/Saved/persistent_server_id"
WORLD_ISLAND_ID_PATH: str = "/srv/windrose/R5/Saved/world_island_id"
WORLDS_PATH_TEMPLATE: str = (
    "/srv/windrose/R5/Saved/SaveProfiles/Default/RocksDB_v2/{game_version}/Worlds"
)
CONFIG_PHASE_FINISHED_LOG_LINE: str = "ServerDescription.json modified"
CONFIG_PHASE_TIMEOUT: float = 180.0
FIRST_WORLD_ISLAND_ID: str = "AAAA37B925C493C86998DADB3D5CA90A"
SECOND_WORLD_ISLAND_ID: str = "BBBB37B925C493C86998DADB3D5CA90B"


@pytest.fixture()
def container(
    podman_client: DockerClient, published_image: PublishedImage
) -> Generator[Container, Any]:
    """Run a container from the built image with the default entrypoint.

    :param podman_client:
    :param published_image:
    :return:
    """
    container: Container = podman_client.container.run(
        published_image.image_reference_latest, detach=True
    )
    yield container
    podman_client.container.remove(container, force=True, volumes=True)


def wait_for_config_phase(
    podman_client: DockerClient, container: Container, start_count: int
) -> None:
    """Wait until start.sh finished updating ServerDescription.json.

    Container logs are preserved across restarts, so the log line appears once
    per container start.

    :param podman_client:
    :param container:
    :param start_count: number of container starts to wait for
    :return:
    """
    deadline: float = time.monotonic() + CONFIG_PHASE_TIMEOUT
    while time.monotonic() < deadline:
        logs: str = podman_client.container.logs(container)
        if logs.count(CONFIG_PHASE_FINISHED_LOG_LINE) >= start_count:
            return
        time.sleep(1)
    pytest.fail(
        f"Container did not finish the configuration phase {start_count} "
        f"time(s) within {CONFIG_PHASE_TIMEOUT} seconds"
    )


def read_container_file(
    podman_client: DockerClient, container: Container, path: str
) -> str:
    """Read a file from the running container.

    :param podman_client:
    :param container:
    :param path:
    :return:
    """
    return str(podman_client.container.execute(container, ["cat", path]))


def read_server_description(podman_client: DockerClient, container: Container) -> dict:
    """Read and parse ServerDescription.json from the running container.

    :param podman_client:
    :param container:
    :return:
    """
    return json.loads(
        read_container_file(podman_client, container, SERVER_DESCRIPTION_PATH)
    )


def test_persistent_ids_survive_container_restarts(
    podman_client: DockerClient, container: Container
) -> None:
    """Test that PersistentServerId and WorldIslandId persist across restarts.

    :param podman_client:
    :param container:
    :return:
    """
    # First start: a new PersistentServerId is generated and persisted.
    wait_for_config_phase(podman_client, container, start_count=1)
    server_description: dict = read_server_description(podman_client, container)
    persistent_server_id: str = server_description["ServerDescription_Persistent"][
        "PersistentServerId"
    ]

    assert re.fullmatch(r"[0-9A-F]{32}", persistent_server_id)
    assert (
        read_container_file(podman_client, container, PERSISTENT_SERVER_ID_PATH).strip()
        == persistent_server_id
    )

    # Simulate the world the server generates on its first start.
    game_version: str = get_game_version(server_description)
    worlds_path: str = WORLDS_PATH_TEMPLATE.format(game_version=game_version)
    podman_client.container.execute(
        container, ["mkdir", "-p", f"{worlds_path}/{FIRST_WORLD_ISLAND_ID}"]
    )

    # Second start: the PersistentServerId is reused and the WorldIslandId is
    # pinned to the single existing world and persisted.
    podman_client.container.restart(container, time=1)
    wait_for_config_phase(podman_client, container, start_count=2)
    server_description = read_server_description(podman_client, container)

    assert (
        server_description["ServerDescription_Persistent"]["PersistentServerId"]
        == persistent_server_id
    )
    assert (
        server_description["ServerDescription_Persistent"]["WorldIslandId"]
        == FIRST_WORLD_ISLAND_ID
    )
    assert (
        read_container_file(podman_client, container, WORLD_ISLAND_ID_PATH).strip()
        == FIRST_WORLD_ISLAND_ID
    )

    # Simulate an additional world, e.g. an imported save game.
    podman_client.container.execute(
        container, ["mkdir", "-p", f"{worlds_path}/{SECOND_WORLD_ISLAND_ID}"]
    )

    # Third start: with multiple worlds the persisted WorldIslandId must win,
    # so the server keeps loading the same world.
    podman_client.container.restart(container, time=1)
    wait_for_config_phase(podman_client, container, start_count=3)
    server_description = read_server_description(podman_client, container)

    assert (
        server_description["ServerDescription_Persistent"]["PersistentServerId"]
        == persistent_server_id
    )
    assert (
        server_description["ServerDescription_Persistent"]["WorldIslandId"]
        == FIRST_WORLD_ISLAND_ID
    )
