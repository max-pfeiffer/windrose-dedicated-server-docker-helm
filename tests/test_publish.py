"""Unit tests for build.publish module."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from build.publish import main
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

FAKE_BUILD_TAG: str = "0.10.0.7.33-372c3516"
FAKE_REGISTRY: str = "localhost:5000"
FAKE_USERNAME: str = "testuser"
FAKE_TOKEN: str = "testtoken"
FAKE_CONTEXT: Path = Path("/fake/build")
FAKE_IMAGE_REFERENCE_VERSION: str = (
    f"{FAKE_REGISTRY}/pfeiffermax/windrose-dedicated-server:{FAKE_BUILD_TAG}"
)
FAKE_IMAGE_REFERENCE_LATEST: str = (
    f"{FAKE_REGISTRY}/pfeiffermax/windrose-dedicated-server:latest"
)
FAKE_BUILD_LOG: list[str] = ["fake build log line\n"]

_BASE_ENV: dict[str, str] = {
    "DOCKER_HUB_USERNAME": FAKE_USERNAME,
    "DOCKER_HUB_TOKEN": FAKE_TOKEN,
    "REGISTRY": FAKE_REGISTRY,
}


@pytest.fixture()
def patch_publish_dependencies(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
) -> Generator[MagicMock]:
    """Patch all external dependencies of ``main`` and yield the Podman client mock.

    Pass ``True`` via ``indirect`` parametrize to simulate an already-published
    image (``tag_exists`` returns ``True``); the default is ``False``.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param request: pytest introspection fixture; ``request.param`` carries the
        ``tag_exists`` return value when the fixture is used with ``indirect``.
    :type request: pytest.FixtureRequest
    :return: Yields ``mock_podman_client``.
    :rtype: collections.abc.Generator[unittest.mock.MagicMock, None, None]
    """
    tag_exists_value: bool = getattr(request, "param", False)

    mocker.patch(
        "build.publish.get_official_image_build_tag", return_value=FAKE_BUILD_TAG
    )
    mocker.patch("build.publish.tag_exists", return_value=tag_exists_value)
    mocker.patch("build.publish.get_context", return_value=FAKE_CONTEXT)
    mocker.patch(
        "build.publish.get_image_reference",
        side_effect=lambda registry, tag: (
            FAKE_IMAGE_REFERENCE_VERSION
            if tag == FAKE_BUILD_TAG
            else FAKE_IMAGE_REFERENCE_LATEST
        ),
    )
    mock_podman_client: MagicMock = MagicMock()
    mock_podman_client.buildx.build.return_value = iter(FAKE_BUILD_LOG)
    mocker.patch("build.publish.get_podman_client", return_value=mock_podman_client)

    yield mock_podman_client


@pytest.mark.parametrize(
    ("patch_publish_dependencies", "publish_manually_env", "expect_build"),
    [
        (False, None, True),
        (True, None, False),
        (False, "1", True),
        (True, "1", True),
    ],
    indirect=["patch_publish_dependencies"],
    ids=["no-tag-builds", "tag-skips", "manual-no-tag-builds", "manual-overrides-tag"],
)
def test_main_build_decision(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
    publish_manually_env: str | None,
    expect_build: bool,
) -> None:
    """Verify build decision logic based on ``publish_manually`` flag and tag existence.

    When a tag already exists and ``--publish-manually`` is not set the build must
    be skipped.  In every other case the container image must be built and pushed.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``;
        parametrized via ``indirect`` with the ``tag_exists`` return value.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :param publish_manually_env: Value for the ``PUBLISH_MANUALLY`` env var, or
        ``None`` to leave it unset.
    :type publish_manually_env: str | None
    :param expect_build: Whether :meth:`DockerClient.buildx.build` should be called.
    :type expect_build: bool
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    env: dict[str, str] = dict(_BASE_ENV)
    if publish_manually_env is not None:
        env["PUBLISH_MANUALLY"] = publish_manually_env

    result: Result = cli_runner.invoke(main, env=env)

    assert result.exit_code == 0
    if expect_build:
        mock_podman_client.buildx.build.assert_called_once()
        mock_podman_client.push.assert_called_once()
    else:
        mock_podman_client.buildx.build.assert_not_called()
        mock_podman_client.push.assert_not_called()


def test_main_registry_login_called_with_credentials(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that registry login uses the registry, username, and token from env vars.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    mock_podman_client.login.assert_called_once_with(
        server=FAKE_REGISTRY,
        username=FAKE_USERNAME,
        password=FAKE_TOKEN,
    )


def test_main_build_uses_correct_tags(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that :meth:`buildx.build` receives both the version and latest tags.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_podman_client.buildx.build.call_args
    assert FAKE_IMAGE_REFERENCE_VERSION in kwargs["tags"]
    assert FAKE_IMAGE_REFERENCE_LATEST in kwargs["tags"]


def test_main_build_targets_linux_amd64(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that the container image is built for the ``linux/amd64`` platform.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_podman_client.buildx.build.call_args
    assert "linux/amd64" in kwargs["platforms"]


def test_main_build_uses_containerfile(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that :meth:`buildx.build` uses the Containerfile from the build context.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_podman_client.buildx.build.call_args
    assert kwargs["file"] == FAKE_CONTEXT / "Containerfile"


def test_main_push_is_called_with_both_tags(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that both image references are pushed to the registry after the build.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    mock_podman_client.push.assert_called_once_with(
        [FAKE_IMAGE_REFERENCE_VERSION, FAKE_IMAGE_REFERENCE_LATEST]
    )


def test_main_build_uses_correct_context(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that :meth:`buildx.build` receives the path from :func:`get_context`.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_podman_client.buildx.build.call_args
    assert kwargs["context_path"] == FAKE_CONTEXT


def test_main_build_streams_logs(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that the build streams its logs and they end up in the CLI output.

    ``stream_logs=True`` is required with Podman: it keeps python_on_whales from
    inspecting buildx builders, which Podman does not provide.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_podman_client = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_podman_client.buildx.build.call_args
    assert kwargs["stream_logs"] is True
    assert FAKE_BUILD_LOG[0] in result.output


def test_main_output_contains_build_tag(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that the CLI output includes the current Windrose server build tag.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    assert FAKE_BUILD_TAG in result.output


@pytest.mark.parametrize("patch_publish_dependencies", [True], indirect=True)
def test_main_output_skip_message_when_tag_exists(
    patch_publish_dependencies: MagicMock,
    cli_runner: CliRunner,
) -> None:
    """Verify that the CLI prints a skip message when the image tag already exists.

    :param patch_publish_dependencies: Fixture yielding ``mock_podman_client``;
        parametrized via ``indirect`` with ``True`` so that :func:`tag_exists`
        returns ``True``.
    :type patch_publish_dependencies: unittest.mock.MagicMock
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    assert "Skipping" in result.output
