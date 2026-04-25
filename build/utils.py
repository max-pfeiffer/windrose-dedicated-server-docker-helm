"""Utilities for image publishing."""

from pathlib import Path

import requests
from steam.client import SteamClient


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


def tag_exists(build_id: str) -> bool:
    """Pull tag data from Docker Hub and check if tag with this build_id already exists.

    :param build_id:
    :return:
    """
    response = requests.get(
        "https://hub.docker.com/v2/namespaces/pfeiffermax/repositories/windrose-dedicated-server/tags"
    )
    response.raise_for_status()
    tags: dict = response.json()["results"]
    matching_tags: list[dict] = [tag for tag in tags if (build_id in tag["name"])]
    if matching_tags:
        return True
    else:
        return False


def create_tag(build_id: str) -> str:
    """Create the Docker image tag.

    :param build_id:
    :return:
    """
    return f"build-{build_id}"
