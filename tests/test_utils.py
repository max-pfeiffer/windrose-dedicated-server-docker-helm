"""Unit tests for build.utils module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests
from build.utils import (
    create_tag,
    get_context,
    get_image_reference,
    get_windrose_build_id,
    tag_exists,
)
from pytest_mock import MockerFixture

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
    ("results", "build_id", "expected"),
    [
        (
            [{"name": f"build-{FAKE_BUILD_ID}"}, {"name": "latest"}],
            FAKE_BUILD_ID,
            True,
        ),
        (
            [{"name": "build-11111"}, {"name": "latest"}],
            FAKE_BUILD_ID,
            False,
        ),
        (
            [],
            FAKE_BUILD_ID,
            False,
        ),
    ],
    ids=["tag-present", "tag-absent", "empty-results"],
)
def test_tag_exists(
    mocker: MockerFixture,
    results: list[dict],
    build_id: str,
    expected: bool,
) -> None:
    """Verify that ``tag_exists`` correctly detects whether a build tag is published.

    :param mocker: pytest-mock fixture providing patching helpers.
    :type mocker: pytest_mock.MockerFixture
    :param results: Simulated ``results`` list returned by the Docker Hub tags API.
    :type results: list[dict]
    :param build_id: Build ID to search for among the tags.
    :type build_id: str
    :param expected: Expected return value of :func:`tag_exists`.
    :type expected: bool
    :return: None
    :rtype: None
    """
    mock_response: MagicMock = MagicMock()
    mock_response.json.return_value = {"results": results}
    mocker.patch("build.utils.requests.get", return_value=mock_response)

    result: bool = tag_exists(build_id)

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
