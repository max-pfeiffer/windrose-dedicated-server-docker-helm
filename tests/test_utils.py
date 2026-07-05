"""Unit tests for build.utils module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests
from build.utils import (
    create_tag,
    get_context,
    get_docker_hub_tags,
    get_image_reference,
    get_official_image_build_tag,
    get_podman_client,
    get_windrose_build_id,
    official_image_latest_tag_changed,
    tag_exists,
)
from pytest_mock import MockerFixture
from python_on_whales import DockerClient

FAKE_BUILD_ID: str = "98765"

_STEAM_PRODUCT_INFO: dict = {
    "apps": {4129620: {"depots": {"branches": {"public": {"buildid": FAKE_BUILD_ID}}}}}
}


def test_get_context_returns_path() -> None:
    """Verify that ``get_context`` returns a :class:`pathlib.Path` instance.

    :return: None
    :rtype: None
    """
    result: Path = get_context()
    assert isinstance(result, Path)


def test_get_context_points_to_build_directory() -> None:
    """Verify that ``get_context`` resolves to the ``build`` directory.

    :return: None
    :rtype: None
    """
    result: Path = get_context()
    assert result.name == "build"


def test_get_context_is_absolute() -> None:
    """Verify that ``get_context`` returns an absolute path.

    :return: None
    :rtype: None
    """
    result: Path = get_context()
    assert result.is_absolute()


@pytest.mark.parametrize(
    ("registry", "tag", "expected"),
    [
        (
            "registry.example.com",
            "latest",
            "registry.example.com/pfeiffermax/windrose-dedicated-server:latest",
        ),
        (
            "localhost:5000",
            f"build-{FAKE_BUILD_ID}",
            f"localhost:5000/pfeiffermax/windrose-dedicated-server:build-{FAKE_BUILD_ID}",
        ),
        (
            "ghcr.io/myorg",
            "build-11111",
            "ghcr.io/myorg/pfeiffermax/windrose-dedicated-server:build-11111",
        ),
    ],
    ids=["docker-hub-latest", "local-registry-build-tag", "ghcr-build-tag"],
)
def test_get_image_reference(registry: str, tag: str, expected: str) -> None:
    """Verify that ``get_image_reference`` produces the correct reference string.

    The reference must follow the pattern
    ``<registry>/pfeiffermax/windrose-dedicated-server:<tag>``.

    :param registry: Docker registry host used as the reference prefix.
    :type registry: str
    :param tag: Image tag to append to the reference.
    :type tag: str
    :param expected: Expected fully-qualified image reference.
    :type expected: str
    :return: None
    :rtype: None
    """
    result: str = get_image_reference(registry, tag)
    assert result == expected


def test_get_windrose_build_id_returns_build_id(mocker: MockerFixture) -> None:
    """Verify that ``get_windrose_build_id`` returns the public branch build ID.

    The Steam client is replaced with a :class:`unittest.mock.MagicMock` so the
    test runs without a live Steam connection.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :return: None
    :rtype: None
    """
    mock_client: MagicMock = MagicMock()
    mock_client.get_product_info.return_value = _STEAM_PRODUCT_INFO
    mocker.patch("build.utils.SteamClient", return_value=mock_client)

    result: str = get_windrose_build_id()

    assert isinstance(result, str)
    assert result == FAKE_BUILD_ID


def test_get_windrose_build_id_uses_anonymous_login(mocker: MockerFixture) -> None:
    """Verify that ``get_windrose_build_id`` authenticates via anonymous login.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :return: None
    :rtype: None
    """
    mock_client: MagicMock = MagicMock()
    mock_client.get_product_info.return_value = _STEAM_PRODUCT_INFO
    mocker.patch("build.utils.SteamClient", return_value=mock_client)

    get_windrose_build_id()

    mock_client.anonymous_login.assert_called_once()


@pytest.mark.parametrize(
    ("results", "tag", "expected"),
    [
        (
            [{"name": "0.10.0.7.33-372c3516"}, {"name": "latest"}],
            "0.10.0.7.33-372c3516",
            True,
        ),
        (
            [{"name": "0.9.0.0-11111111"}, {"name": "latest"}],
            "0.10.0.7.33-372c3516",
            False,
        ),
        (
            [{"name": "0.10.0.7.33-372c3516-hotfix"}, {"name": "latest"}],
            "0.10.0.7.33-372c3516",
            False,
        ),
        (
            [],
            "0.10.0.7.33-372c3516",
            False,
        ),
    ],
    ids=["tag-present", "tag-absent", "no-substring-match", "empty-results"],
)
def test_tag_exists(
    mocker: MockerFixture,
    results: list[dict],
    tag: str,
    expected: bool,
) -> None:
    """Verify that ``tag_exists`` detects a published tag by exact name match.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param results: Simulated tag list returned by :func:`get_docker_hub_tags`.
    :type results: list[dict]
    :param tag: Tag name to search for among the published tags.
    :type tag: str
    :param expected: Expected return value of :func:`tag_exists`.
    :type expected: bool
    :return: None
    :rtype: None
    """
    mocker.patch("build.utils.get_docker_hub_tags", return_value=results)

    result: bool = tag_exists(tag)

    assert result is expected


def test_tag_exists_raises_on_http_error(mocker: MockerFixture) -> None:
    """Verify that ``tag_exists`` propagates error on bad HTTP responses.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :raises requests.HTTPError: when the Docker Hub API returns a non-2xx status.
    :return: None
    :rtype: None
    """
    mock_response: MagicMock = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    mocker.patch("build.utils.requests.get", return_value=mock_response)

    with pytest.raises(requests.HTTPError):
        tag_exists(FAKE_BUILD_ID)


def test_get_podman_client_uses_default_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that ``get_podman_client`` uses plain Podman without a connection.

    :param monkeypatch: pytest fixture for patching the environment.
    :type monkeypatch: pytest.MonkeyPatch
    :return: None
    :rtype: None
    """
    monkeypatch.delenv("PODMAN_CONNECTION", raising=False)

    result: DockerClient = get_podman_client()

    assert result.client_config.client_call == ["podman"]


def test_get_podman_client_uses_podman_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that ``get_podman_client`` honors the PODMAN_CONNECTION env var.

    :param monkeypatch: pytest fixture for patching the environment.
    :type monkeypatch: pytest.MonkeyPatch
    :return: None
    :rtype: None
    """
    monkeypatch.setenv("PODMAN_CONNECTION", "remotebuilder")

    result: DockerClient = get_podman_client()

    assert result.client_config.client_call == [
        "podman",
        "--connection",
        "remotebuilder",
    ]


@pytest.mark.parametrize(
    "build_id",
    ["12345", "98765", "54321", "00001"],
    ids=["five-digits", "build-id-98765", "reversed-digits", "leading-zeros"],
)
def test_create_tag(build_id: str) -> None:
    """Verify that ``create_tag`` returns a build_id string for any build ID.

    :param build_id: The build identifier to embed in the tag.
    :type build_id: str
    :return: None
    :rtype: None
    """
    result: str = create_tag(build_id)

    assert isinstance(result, str)
    assert result == f"build-{build_id}"
    assert build_id in result


FAKE_BUILD_TAG: str = "0.10.0.7.33-372c3516"
FAKE_DIGEST: str = "sha256:754336a4bb4807e4471727da9700e10a7c48fe618fb45612102ff05a"

_OFFICIAL_IMAGE_TAGS: list[dict] = [
    {
        "name": "latest",
        "digest": FAKE_DIGEST,
        "tag_last_pushed": "2026-06-24T18:41:03.178504Z",
    },
    {
        "name": FAKE_BUILD_TAG,
        "digest": FAKE_DIGEST,
        "tag_last_pushed": "2026-06-24T18:40:57.230328Z",
    },
    {
        "name": "0.10.0.7.0-6-hotfix-e371b7e4",
        "digest": "sha256:d1fbd9cdfb765ceae49eafdc3b6f9cae0cd22e08fc09ff9a606ff7",
        "tag_last_pushed": "2026-05-21T10:07:00.376949Z",
    },
]


def test_get_docker_hub_tags_follows_pagination(mocker: MockerFixture) -> None:
    """Verify that ``get_docker_hub_tags`` collects tags across result pages.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :return: None
    :rtype: None
    """
    first_response: MagicMock = MagicMock()
    first_response.json.return_value = {
        "results": [{"name": "latest"}],
        "next": "https://hub.docker.com/v2/some-next-page",
    }
    second_response: MagicMock = MagicMock()
    second_response.json.return_value = {
        "results": [{"name": FAKE_BUILD_TAG}],
        "next": None,
    }
    mock_get: MagicMock = mocker.patch(
        "build.utils.requests.get",
        side_effect=[first_response, second_response],
    )

    result: list[dict] = get_docker_hub_tags("windroseserver", "windroseserver")

    assert result == [{"name": "latest"}, {"name": FAKE_BUILD_TAG}]
    assert mock_get.call_count == 2


def test_get_docker_hub_tags_raises_on_http_error(mocker: MockerFixture) -> None:
    """Verify that ``get_docker_hub_tags`` propagates error on bad HTTP responses.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :raises requests.HTTPError: when the Docker Hub API returns a non-2xx status.
    :return: None
    :rtype: None
    """
    mock_response: MagicMock = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    mocker.patch("build.utils.requests.get", return_value=mock_response)

    with pytest.raises(requests.HTTPError):
        get_docker_hub_tags("windroseserver", "windroseserver")


def test_get_official_image_build_tag(mocker: MockerFixture) -> None:
    """Verify that the build tag matching the latest tag's digest is returned.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :return: None
    :rtype: None
    """
    mocker.patch(
        "build.utils.get_docker_hub_tags",
        return_value=_OFFICIAL_IMAGE_TAGS,
    )

    result: str = get_official_image_build_tag()

    assert result == FAKE_BUILD_TAG


def test_get_official_image_build_tag_picks_most_recent(
    mocker: MockerFixture,
) -> None:
    """Verify that the most recently pushed matching build tag wins.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :return: None
    :rtype: None
    """
    tags: list[dict] = [
        *_OFFICIAL_IMAGE_TAGS,
        {
            "name": "older-build-tag",
            "digest": FAKE_DIGEST,
            "tag_last_pushed": "2026-01-01T00:00:00.000000Z",
        },
    ]
    mocker.patch("build.utils.get_docker_hub_tags", return_value=tags)

    result: str = get_official_image_build_tag()

    assert result == FAKE_BUILD_TAG


@pytest.mark.parametrize(
    "tags",
    [
        [{"name": FAKE_BUILD_TAG, "digest": FAKE_DIGEST, "tag_last_pushed": ""}],
        [{"name": "latest", "digest": FAKE_DIGEST, "tag_last_pushed": ""}],
        [],
    ],
    ids=["no-latest-tag", "no-matching-build-tag", "no-tags"],
)
def test_get_official_image_build_tag_raises(
    mocker: MockerFixture,
    tags: list[dict],
) -> None:
    """Verify that missing latest or build tags raise a :class:`RuntimeError`.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param tags: Simulated tag list returned by the Docker Hub tags API.
    :type tags: list[dict]
    :raises RuntimeError: when the latest tag or a matching build tag is missing.
    :return: None
    :rtype: None
    """
    mocker.patch("build.utils.get_docker_hub_tags", return_value=tags)

    with pytest.raises(RuntimeError):
        get_official_image_build_tag()


@pytest.mark.parametrize(
    ("published_tags", "expected"),
    [
        (
            [{"name": FAKE_BUILD_TAG}, {"name": "latest"}],
            False,
        ),
        (
            [{"name": "0.9.0.0-11111111"}, {"name": "latest"}],
            True,
        ),
        (
            [],
            True,
        ),
    ],
    ids=["tag-published", "tag-not-published", "no-tags-published"],
)
def test_official_image_latest_tag_changed(
    mocker: MockerFixture,
    published_tags: list[dict],
    expected: bool,
) -> None:
    """Verify change detection against the published image tags.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param published_tags: Simulated tags of pfeiffermax/windrose-dedicated-server.
    :type published_tags: list[dict]
    :param expected: Expected return value of
        :func:`official_image_latest_tag_changed`.
    :type expected: bool
    :return: None
    :rtype: None
    """
    mocker.patch(
        "build.utils.get_docker_hub_tags",
        side_effect=[_OFFICIAL_IMAGE_TAGS, published_tags],
    )

    result: bool = official_image_latest_tag_changed()

    assert result is expected
