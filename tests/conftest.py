"""Test fixtures."""

from collections.abc import Generator
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from typing import Any

import pytest


@pytest.fixture(scope="session")
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
        yield server_description_path
