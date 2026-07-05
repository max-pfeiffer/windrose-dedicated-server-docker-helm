"""Utilities for image publishing."""

import os
from pathlib import Path

import requests
from python_on_whales import DockerClient
from steam.client import SteamClient


def get_podman_client() -> DockerClient:
    """Return the Python on Whales client configured for Podman.

    If the PODMAN_CONNECTION environment variable is set, the client uses
    that Podman system connection. This way a remote Podman host can build
    and run the linux/amd64 image, e.g. when working on an arm64 machine.

    :return:
    """
    client_call: list[str] = ["podman"]
    podman_connection: str | None = os.environ.get("PODMAN_CONNECTION")
    if podman_connection:
        client_call += ["--connection", podman_connection]
    return DockerClient(client_call=client_call, client_type="podman")


def get_context() -> Path:
    """Return Docker build context.

    :return:
    """
    return Path(__file__).parent.resolve()


def get_image_reference(
    registry: str,
    tag: str,
) -> str:
    """Return image reference.

    :param registry:
    :param image_version:
    :return:
    """
    reference: str = f"{registry}/pfeiffermax/windrose-dedicated-server:{tag}"
    return reference


def get_windrose_build_id() -> str:
    """Pull the Valheim server's build ID using the Steam Client.

    :return:
    """
    client = SteamClient()
    client.anonymous_login()
    client.verbose_debug = False
    info: dict = client.get_product_info(apps=[4129620], timeout=1)
    build_id: str = info["apps"][4129620]["depots"]["branches"]["public"]["buildid"]
    return build_id


def tag_exists(tag: str) -> bool:
    """Check if pfeiffermax/windrose-dedicated-server already has this tag.

    :param tag:
    :return:
    """
    tags: list[dict] = get_docker_hub_tags("pfeiffermax", "windrose-dedicated-server")
    tag_names: set[str] = {existing_tag["name"] for existing_tag in tags}
    return tag in tag_names


def create_tag(build_id: str) -> str:
    """Create the Docker image tag.

    :param build_id:
    :return:
    """
    return f"build-{build_id}"


def get_docker_hub_tags(namespace: str, repository: str) -> list[dict]:
    """Pull all tag data of a Docker Hub repository.

    Follows pagination, so the result is complete even for repositories
    with more tags than fit on a single API result page.

    :param namespace:
    :param repository:
    :return:
    """
    tags: list[dict] = []
    url: str | None = (
        f"https://hub.docker.com/v2/namespaces/{namespace}"
        f"/repositories/{repository}/tags?page_size=100"
    )
    while url:
        response = requests.get(url)
        response.raise_for_status()
        data: dict = response.json()
        tags += data["results"]
        url = data["next"]
    return tags


def get_official_image_build_tag() -> str:
    """Return the build tag the official image's latest tag points to.

    The windroseserver/windroseserver repository tags every image with a
    version/build ID tag (e.g. 0.10.0.7.33-372c3516) and moves the latest
    tag to the same digest. Resolving the digest of the latest tag to its
    companion tag reliably identifies the build the latest tag points to.

    :return:
    """
    tags: list[dict] = get_docker_hub_tags("windroseserver", "windroseserver")
    latest_tag: dict | None = next(
        (tag for tag in tags if tag["name"] == "latest"), None
    )
    if latest_tag is None:
        raise RuntimeError(
            "No latest tag found for windroseserver/windroseserver on Docker Hub"
        )
    build_tags: list[dict] = [
        tag
        for tag in tags
        if tag["name"] != "latest" and tag["digest"] == latest_tag["digest"]
    ]
    if not build_tags:
        raise RuntimeError(
            "No build tag found matching the digest of "
            "windroseserver/windroseserver:latest"
        )
    build_tags.sort(key=lambda tag: tag["tag_last_pushed"], reverse=True)
    return build_tags[0]["name"]


def official_image_latest_tag_changed() -> bool:
    """Check if the latest tag of windroseserver/windroseserver changed.

    Resolves the build tag windroseserver/windroseserver:latest currently
    points to and checks if pfeiffermax/windrose-dedicated-server already
    has an image with that tag.

    :return: True if the build tag is not published yet for
        pfeiffermax/windrose-dedicated-server, False otherwise.
    """
    return not tag_exists(get_official_image_build_tag())
