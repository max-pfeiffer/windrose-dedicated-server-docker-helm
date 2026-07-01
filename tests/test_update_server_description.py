"""Tests for Updating Server Description."""

import json
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from build.scripts.update_server_description import (
    get_persistent_server_id,
    get_world_island_id,
    main,
    parse_args,
)
from pytest import MonkeyPatch
from pytest_mock import MockerFixture


def test_get_persistent_server_id_from_file(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Reuse the id persisted on the data volume from a previous start.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    id_file = tmp_path / "persistent_server_id"
    id_file.write_text("PERSISTED_SERVER_ID\n")
    monkeypatch.setenv("PERSISTENT_SERVER_ID_FILE", str(id_file))
    assert get_persistent_server_id() == "PERSISTED_SERVER_ID"


def test_get_persistent_server_id_generated(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Generate a new id and persist it when none exists yet.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    id_file = tmp_path / "subdir" / "persistent_server_id"
    monkeypatch.setenv("PERSISTENT_SERVER_ID_FILE", str(id_file))

    persistent_server_id = get_persistent_server_id()

    assert re.fullmatch(r"[0-9A-F]{32}", persistent_server_id)
    assert id_file.read_text() == persistent_server_id
    # A subsequent call returns the same persisted id.
    assert get_persistent_server_id() == persistent_server_id


def test_get_world_island_id_from_environment(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Use the world from the environment variable and persist it.

    The environment variable takes precedence over a previously persisted id.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    id_file = tmp_path / "world_island_id"
    id_file.write_text("OLD_WORLD")
    monkeypatch.setenv("WORLD_ISLAND_ID_FILE", str(id_file))
    monkeypatch.setenv("WORLD_ISLAND_ID", "IMPORTED_WORLD")

    assert get_world_island_id(["OLD_WORLD", "IMPORTED_WORLD"]) == "IMPORTED_WORLD"
    assert id_file.read_text() == "IMPORTED_WORLD"


def test_get_world_island_id_from_environment_not_existing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Fail if the world from the environment variable does not exist.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    monkeypatch.setenv("WORLD_ISLAND_ID_FILE", str(tmp_path / "world_island_id"))
    monkeypatch.setenv("WORLD_ISLAND_ID", "MISSING_WORLD")

    with pytest.raises(SystemExit):
        get_world_island_id(["EXISTING_WORLD"])


def test_get_world_island_id_from_file(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Reuse the id persisted on the data volume from a previous start.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    id_file = tmp_path / "world_island_id"
    id_file.write_text("PERSISTED_WORLD\n")
    monkeypatch.setenv("WORLD_ISLAND_ID_FILE", str(id_file))

    assert (
        get_world_island_id(["PERSISTED_WORLD", "IMPORTED_WORLD"]) == "PERSISTED_WORLD"
    )


def test_get_world_island_id_from_file_not_existing(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Fail if the persisted world does not exist anymore.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    id_file = tmp_path / "world_island_id"
    id_file.write_text("PERSISTED_WORLD")
    monkeypatch.setenv("WORLD_ISLAND_ID_FILE", str(id_file))

    with pytest.raises(SystemExit):
        get_world_island_id(["OTHER_WORLD"])


def test_get_world_island_id_no_worlds(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Let the server generate a new world if none exists yet.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    id_file = tmp_path / "world_island_id"
    monkeypatch.setenv("WORLD_ISLAND_ID_FILE", str(id_file))

    assert get_world_island_id([]) is None
    assert not id_file.exists()


def test_get_world_island_id_single_world(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Use the single existing world and persist it.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    id_file = tmp_path / "subdir" / "world_island_id"
    monkeypatch.setenv("WORLD_ISLAND_ID_FILE", str(id_file))

    assert get_world_island_id(["SINGLE_WORLD"]) == "SINGLE_WORLD"
    assert id_file.read_text() == "SINGLE_WORLD"


def test_get_world_island_id_multiple_worlds(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Fail if the world cannot be determined from multiple worlds.

    :param tmp_path:
    :param monkeypatch:
    :return:
    """
    monkeypatch.setenv("WORLD_ISLAND_ID_FILE", str(tmp_path / "world_island_id"))

    with pytest.raises(SystemExit):
        get_world_island_id(["WORLD_A", "WORLD_B"])


def test_argument_parser(server_description_path: Path):
    """Test the argument parser.

    :param server_description_path:
    :return:
    """
    parser = parse_args([str(server_description_path)])
    assert parser.server_description == str(server_description_path)


@pytest.mark.parametrize(
    "fake_invite_code,fake_password,fake_server_name,fake_max_player_count,"
    "fake_user_selected_region,fake_p2p_proxy_address,fake_use_direct_connection,"
    "fake_direct_connection_server_address,fake_direct_connection_server_port,"
    "fake_direct_connection_proxy_address,expected_result",
    [
        (
            "fake_invite_code",
            "fake_password",
            "fake_server_name",
            "5",
            "fake_user_selected_region",
            "fake_p2p_proxy_address",
            "true",
            "fake_direct_connection_server_address",
            "28050",
            "fake_direct_connection_proxy_address",
            {
                "Version": 1,
                "DeploymentId": "0.10.0.3.104-256f9653",
                "ServerDescription_Persistent": {
                    "PersistentServerId": "FAKE_PERSISTENT_SERVER_ID",
                    "InviteCode": "fake_invite_code",
                    "IsPasswordProtected": True,
                    "Password": "fake_password",
                    "ServerName": "fake_server_name",
                    "WorldIslandId": "1EDB437B925C493C86998DADB3D5CA90",
                    "MaxPlayerCount": 5,
                    "UserSelectedRegion": "fake_user_selected_region",
                    "P2pProxyAddress": "fake_p2p_proxy_address",
                    "UseDirectConnection": True,
                    "DirectConnectionServerAddress": "fake_direct_connection_"
                    "server_address",
                    "DirectConnectionServerPort": 28050,
                    "DirectConnectionProxyAddress": "fake_direct_connection_"
                    "proxy_address",
                },
            },
        ),
        (
            "fake_invite_code",
            "",
            "fake_server_name",
            "5",
            "fake_user_selected_region",
            "fake_p2p_proxy_address",
            "true",
            "fake_direct_connection_server_address",
            "28050",
            "fake_direct_connection_proxy_address",
            {
                "Version": 1,
                "DeploymentId": "0.10.0.3.104-256f9653",
                "ServerDescription_Persistent": {
                    "PersistentServerId": "FAKE_PERSISTENT_SERVER_ID",
                    "InviteCode": "fake_invite_code",
                    "IsPasswordProtected": False,
                    "Password": "",
                    "ServerName": "fake_server_name",
                    "WorldIslandId": "1EDB437B925C493C86998DADB3D5CA90",
                    "MaxPlayerCount": 5,
                    "UserSelectedRegion": "fake_user_selected_region",
                    "P2pProxyAddress": "fake_p2p_proxy_address",
                    "UseDirectConnection": True,
                    "DirectConnectionServerAddress": "fake_direct_connection"
                    "_server_address",
                    "DirectConnectionServerPort": 28050,
                    "DirectConnectionProxyAddress": "fake_direct_connection"
                    "_proxy_address",
                },
            },
        ),
        (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            {
                "Version": 1,
                "DeploymentId": "0.10.0.3.104-256f9653",
                "ServerDescription_Persistent": {
                    "PersistentServerId": "FAKE_PERSISTENT_SERVER_ID",
                    "InviteCode": "d2be7c90",
                    "IsPasswordProtected": False,
                    "Password": "",
                    "ServerName": "",
                    "WorldIslandId": "1EDB437B925C493C86998DADB3D5CA90",
                    "MaxPlayerCount": 8,
                    "UserSelectedRegion": "",
                    "P2pProxyAddress": "127.0.0.1",
                    "UseDirectConnection": False,
                    "DirectConnectionServerAddress": "",
                    "DirectConnectionServerPort": -1,
                    "DirectConnectionProxyAddress": "0.0.0.0",
                },
            },
        ),
    ],
)
def test_update_server_description(
    server_description_path: Path,
    tmp_path: Path,
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
    fake_invite_code: str | None,
    fake_password: str | None,
    fake_server_name: str | None,
    fake_max_player_count: str | None,
    fake_user_selected_region: str | None,
    fake_p2p_proxy_address: str | None,
    fake_use_direct_connection: str | None,
    fake_direct_connection_server_address: str | None,
    fake_direct_connection_server_port: str | None,
    fake_direct_connection_proxy_address: str | None,
    expected_result: dict,
) -> None:
    """Test updating server description.

    :param server_description_path:
    :param mocker:
    :param monkeypatch:
    :param fake_invite_code:
    :param fake_password:
    :param fake_server_name:
    :param fake_max_player_count:
    :param fake_user_selected_region:
    :param fake_p2p_proxy_address:
    :param fake_use_direct_connection:
    :param fake_direct_connection_server_address:
    :param fake_direct_connection_server_port:
    :param fake_direct_connection_proxy_address:
    :param expected_result:
    :return:
    """
    mocked_args = MagicMock()
    mocked_args.server_description = str(server_description_path)
    mocker.patch(
        "build.scripts.update_server_description.parse_args", return_value=mocked_args
    )

    id_file = tmp_path / "persistent_server_id"
    id_file.write_text("FAKE_PERSISTENT_SERVER_ID")

    with monkeypatch.context() as mp:
        mp.setenv("PERSISTENT_SERVER_ID_FILE", str(id_file))
        mp.setenv("WORLD_ISLAND_ID_FILE", str(tmp_path / "world_island_id"))
        if fake_invite_code is not None:
            mp.setenv("INVITE_CODE", fake_invite_code)
        if fake_password is not None:
            mp.setenv("PASSWORD", fake_password)
        if fake_server_name is not None:
            mp.setenv("SERVER_NAME", fake_server_name)
        if fake_max_player_count is not None:
            mp.setenv("MAX_PLAYER_COUNT", fake_max_player_count)
        if fake_user_selected_region is not None:
            mp.setenv("USER_SELECTED_REGION", fake_user_selected_region)
        if fake_p2p_proxy_address is not None:
            mp.setenv("P2P_PROXY_ADDRESS", fake_p2p_proxy_address)
        if fake_use_direct_connection is not None:
            mp.setenv("USE_DIRECT_CONNECTION", fake_use_direct_connection)
        if fake_direct_connection_server_address is not None:
            mp.setenv(
                "DIRECT_CONNECTION_SERVER_ADDRESS",
                fake_direct_connection_server_address,
            )
        if fake_direct_connection_server_port is not None:
            mp.setenv(
                "DIRECT_CONNECTION_SERVER_PORT", fake_direct_connection_server_port
            )
        if fake_direct_connection_proxy_address is not None:
            mp.setenv(
                "DIRECT_CONNECTION_PROXY_ADDRESS", fake_direct_connection_proxy_address
            )
        main()

    with open(server_description_path) as server_description_file:
        server_description = json.load(server_description_file)

    assert server_description == expected_result
