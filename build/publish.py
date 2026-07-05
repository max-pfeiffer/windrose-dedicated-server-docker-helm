"""Publish CLI."""

from pathlib import Path

import click
from python_on_whales import DockerClient

from build.utils import (
    get_context,
    get_image_reference,
    get_official_image_build_tag,
    get_podman_client,
    tag_exists,
)


@click.command()
@click.option(
    "--docker-hub-username",
    envvar="DOCKER_HUB_USERNAME",
    help="Docker Hub username",
)
@click.option(
    "--docker-hub-token",
    envvar="DOCKER_HUB_TOKEN",
    help="Docker Hub token",
)
@click.option(
    "--registry", envvar="REGISTRY", default="docker.io", help="Container registry"
)
@click.option(
    "--publish-manually",
    envvar="PUBLISH_MANUALLY",
    is_flag=True,
    help="Flag for building the container image manually, "
    "overrides the check for existing image tags",
)
def main(
    docker_hub_username: str,
    docker_hub_token: str,
    registry: str,
    publish_manually: bool,
) -> None:
    """Build image with Podman and publish it to Docker Hub.

    :param docker_hub_username:
    :param docker_hub_token:
    :param registry:
    :param publish_manually:
    :return:
    """
    context: Path = get_context()

    click.echo("Checking build tag of the official Windrose server image...")
    current_windrose_server_build_tag: str = get_official_image_build_tag()
    click.echo(
        f"Current Windrose server build tag: {current_windrose_server_build_tag}"
    )

    if not publish_manually and tag_exists(current_windrose_server_build_tag):
        click.echo(
            "Image for this build tag already exists. Skipping container image build..."
        )
    else:
        click.echo("Building Windrose server container image...")

        image_reference_version: str = get_image_reference(
            registry, current_windrose_server_build_tag
        )
        image_reference_latest: str = get_image_reference(registry, "latest")

        podman_client: DockerClient = get_podman_client()

        podman_client.login(
            server=registry,
            username=docker_hub_username,
            password=docker_hub_token,
        )

        # Podman has no --push flag on build, so build and push separately.
        # stream_logs=True keeps python_on_whales from inspecting buildx
        # builders, which Podman's buildx compatibility alias does not provide.
        build_log_stream = podman_client.buildx.build(
            context_path=context,
            file=context / "Containerfile",
            tags=[image_reference_version, image_reference_latest],
            platforms=["linux/amd64"],
            stream_logs=True,
        )
        for log_line in build_log_stream:
            click.echo(log_line, nl=False)

        click.echo("Pushing Windrose server container image...")
        podman_client.push([image_reference_version, image_reference_latest])


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
