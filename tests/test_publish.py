"""Unit tests for build.publish module."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from build.publish import main
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

FAKE_BUILD_ID: str = "98765"
FAKE_TAG: str = f"build-{FAKE_BUILD_ID}"
FAKE_REGISTRY: str = "localhost:5000"
FAKE_USERNAME: str = "testuser"
FAKE_TOKEN: str = "testtoken"
FAKE_CONTEXT: Path = Path("/fake/build")
FAKE_IMAGE_REFERENCE_VERSION: str = (
    f"{FAKE_REGISTRY}/pfeiffermax/windrose-dedicated-server:{FAKE_TAG}"
)
FAKE_IMAGE_REFERENCE_LATEST: str = (
    f"{FAKE_REGISTRY}/pfeiffermax/windrose-dedicated-server:latest"
)

_BASE_ENV: dict[str, str] = {
    "DOCKER_HUB_USERNAME": FAKE_USERNAME,
    "DOCKER_HUB_TOKEN": FAKE_TOKEN,
    "REGISTRY": FAKE_REGISTRY,
}


@pytest.fixture()
def patch_publish_dependencies(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
) -> Generator[tuple[MagicMock, MagicMock]]:
    """Patch all external dependencies of ``main`` and yield the Docker mocks.

    Pass ``True`` via ``indirect`` parametrize to simulate an already-published
    image (``tag_exists`` returns ``True``); the default is ``False``.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param request: pytest introspection fixture; ``request.param`` carries the
        ``tag_exists`` return value when the fixture is used with ``indirect``.
    :type request: pytest.FixtureRequest
    :return: Yields a tuple of ``(mock_docker_client, mock_builder)``.
    :rtype: collections.abc.Generator[tuple[MagicMock, MagicMock], None, None]
    """
    tag_exists_value: bool = getattr(request, "param", False)

    mocker.patch("build.publish.get_windrose_build_id", return_value=FAKE_BUILD_ID)
    mocker.patch("build.publish.tag_exists", return_value=tag_exists_value)
    mocker.patch("build.publish.get_context", return_value=FAKE_CONTEXT)
    mocker.patch("build.publish.create_tag", return_value=FAKE_TAG)
    mocker.patch(
        "build.publish.get_image_reference",
        side_effect=lambda registry, tag: (
            FAKE_IMAGE_REFERENCE_VERSION
            if tag == FAKE_TAG
            else FAKE_IMAGE_REFERENCE_LATEST
        ),
    )
    mock_builder: MagicMock = MagicMock()
    mock_docker_client: MagicMock = MagicMock()
    mock_docker_client.buildx.create.return_value = mock_builder
    mocker.patch("build.publish.DockerClient", return_value=mock_docker_client)

    yield mock_docker_client, mock_builder


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
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
    publish_manually_env: str | None,
    expect_build: bool,
) -> None:
    """Verify build decision logic based on ``publish_manually`` flag and tag existence.

    When a tag already exists and ``--publish-manually`` is not set the build must
    be skipped.  In every other case the Docker image must be built.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``; parametrized via ``indirect`` with
        the ``tag_exists`` return value.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
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
    mock_docker_client, _ = patch_publish_dependencies

    env: dict[str, str] = dict(_BASE_ENV)
    if publish_manually_env is not None:
        env["PUBLISH_MANUALLY"] = publish_manually_env

    result: Result = cli_runner.invoke(main, env=env)

    assert result.exit_code == 0
    if expect_build:
        mock_docker_client.buildx.build.assert_called_once()
    else:
        mock_docker_client.buildx.build.assert_not_called()


def test_main_docker_login_called_with_credentials(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that Docker login uses the registry, username, and token from env vars.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    mock_docker_client.login.assert_called_once_with(
        server=FAKE_REGISTRY,
        username=FAKE_USERNAME,
        password=FAKE_TOKEN,
    )


def test_main_buildx_build_uses_correct_tags(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that :meth:`buildx.build` receives both the version and latest tags.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.build.call_args
    assert FAKE_IMAGE_REFERENCE_VERSION in kwargs["tags"]
    assert FAKE_IMAGE_REFERENCE_LATEST in kwargs["tags"]


def test_main_buildx_build_targets_linux_amd64(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that the Docker image is built for the ``linux/amd64`` platform.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.build.call_args
    assert "linux/amd64" in kwargs["platforms"]


def test_main_buildx_build_uses_production_target(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that :meth:`buildx.build` targets the ``production-image`` stage.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.build.call_args
    assert kwargs["target"] == "production-image"


def test_main_buildx_build_push_is_enabled(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that the image is pushed to the registry after the build.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.build.call_args
    assert kwargs["push"] is True


def test_main_buildx_build_uses_correct_context(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that :meth:`buildx.build` receives the path from :func:`get_context`.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.build.call_args
    assert kwargs["context_path"] == FAKE_CONTEXT


def test_main_builder_created_with_docker_container_driver(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that the buildx builder uses the ``docker-container`` driver.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.create.call_args
    assert kwargs["driver"] == "docker-container"


def test_main_builder_cleanup_after_build(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that the buildx builder is stopped and removed after the image build.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    mock_docker_client, mock_builder = patch_publish_dependencies

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    mock_docker_client.buildx.stop.assert_called_once_with(mock_builder)
    mock_docker_client.buildx.remove.assert_called_once_with(mock_builder)


@pytest.mark.parametrize(
    ("github_ref_name", "expected_cache_type"),
    [
        ("main", "gha"),
        ("feature/my-branch", "gha"),
        (None, "local"),
    ],
    ids=["main-branch-uses-gha", "feature-branch-uses-gha", "no-ref-uses-local"],
)
def test_main_cache_type_based_on_github_ref_name(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    mocker: MockerFixture,
    cli_runner: CliRunner,
    github_ref_name: str | None,
    expected_cache_type: str,
) -> None:
    """Verify GHA cache is used when ``GITHUB_REF_NAME`` is set, otherwise local.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :param github_ref_name: Value returned by ``getenv("GITHUB_REF_NAME")``, or
        ``None`` when the variable is absent.
    :type github_ref_name: str | None
    :param expected_cache_type: Expected ``type=`` prefix in the cache arguments.
    :type expected_cache_type: str
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies
    mocker.patch("build.publish.getenv", return_value=github_ref_name)

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.build.call_args
    assert f"type={expected_cache_type}" in kwargs["cache_to"]
    assert f"type={expected_cache_type}" in kwargs["cache_from"]


@pytest.mark.parametrize(
    "ref_name",
    ["main", "release/1.0.0", "feature/add-thing"],
    ids=["main", "release-branch", "feature-branch"],
)
def test_main_gha_cache_scope_matches_branch(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    mocker: MockerFixture,
    cli_runner: CliRunner,
    ref_name: str,
) -> None:
    """Verify that the GHA cache scope matches the ``GITHUB_REF_NAME`` value.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :param ref_name: Simulated ``GITHUB_REF_NAME`` value.
    :type ref_name: str
    :return: None
    :rtype: None
    """
    mock_docker_client, _ = patch_publish_dependencies
    mocker.patch("build.publish.getenv", return_value=ref_name)

    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    _, kwargs = mock_docker_client.buildx.build.call_args
    assert f"scope={ref_name}" in kwargs["cache_to"]
    assert f"scope={ref_name}" in kwargs["cache_from"]


def test_main_output_contains_build_id(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that the CLI output includes the current Windrose server build ID.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    assert FAKE_BUILD_ID in result.output


@pytest.mark.parametrize("patch_publish_dependencies", [True], indirect=True)
def test_main_output_skip_message_when_tag_exists(
    patch_publish_dependencies: tuple[MagicMock, MagicMock],
    cli_runner: CliRunner,
) -> None:
    """Verify that the CLI prints a skip message when the image tag already exists.

    :param patch_publish_dependencies: Fixture yielding
        ``(mock_docker_client, mock_builder)``; parametrized via ``indirect`` with
        ``True`` so that :func:`tag_exists` returns ``True``.
    :type patch_publish_dependencies: tuple[MagicMock, MagicMock]
    :param cli_runner: Click CLI test runner.
    :type cli_runner: click.testing.CliRunner
    :return: None
    :rtype: None
    """
    result: Result = cli_runner.invoke(main, env=_BASE_ENV)

    assert result.exit_code == 0
    assert "Skipping" in result.output
