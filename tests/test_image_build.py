"""Tests building the container image and publishing it to a registry."""

import pytest
from furl import furl
from requests import Response, get

from tests.conftest import PublishedImage

pytestmark = pytest.mark.slow


def test_image_is_published_to_registry(published_image: PublishedImage) -> None:
    """Test that the built image was pushed with the build and latest tags.

    The image itself is built once per session by the published_image fixture.

    :param published_image:
    :return:
    """
    catalog_url: furl = furl(f"http://{published_image.registry}")
    catalog_url.path /= "v2/_catalog"

    response: Response = get(catalog_url.url)

    assert response.status_code == 200
    assert response.json() == {
        "repositories": ["pfeiffermax/windrose-dedicated-server"]
    }

    tags_url: furl = furl(f"http://{published_image.registry}")
    tags_url.path /= "v2/pfeiffermax/windrose-dedicated-server/tags/list"

    response = get(tags_url.url)

    assert response.status_code == 200

    response_image_tags: list[str] = response.json()["tags"]

    assert published_image.tag in response_image_tags
    assert "latest" in response_image_tags
