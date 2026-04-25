"""Tests for Updating Server Description."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from build.update_server_description import main, parse_args
from pytest import MonkeyPatch
from pytest_mock import MockerFixture


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
                    "PersistentServerId": "9BE66DD44655244015C1B3AC3CE4515A",
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
                    "PersistentServerId": "9BE66DD44655244015C1B3AC3CE4515A",
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
    ],
)
def test_update_server_description(
    server_description_path: Path,
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
    fake_invite_code: str,
    fake_password: str,
    fake_server_name: str,
    fake_max_player_count: str,
    fake_user_selected_region: str,
    fake_p2p_proxy_address: str,
    fake_use_direct_connection: str,
    fake_direct_connection_server_address: str,
    fake_direct_connection_server_port: str,
    fake_direct_connection_proxy_address: str,
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
    mocker.patch("build.update_server_description.parse_args", return_value=mocked_args)

    with monkeypatch.context() as mp:
        mp.setenv("INVITE_CODE", fake_invite_code)
        mp.setenv("PASSWORD", fake_password)
        mp.setenv("SERVER_NAME", fake_server_name)
        mp.setenv("MAX_PLAYER_COUNT", fake_max_player_count)
        mp.setenv("USER_SELECTED_REGION", fake_user_selected_region)
        mp.setenv("P2P_PROXY_ADDRESS", fake_p2p_proxy_address)
        mp.setenv("USE_DIRECT_CONNECTION", fake_use_direct_connection)
        mp.setenv(
            "DIRECT_CONNECTION_SERVER_ADDRESS", fake_direct_connection_server_address
        )
        mp.setenv("DIRECT_CONNECTION_SERVER_PORT", fake_direct_connection_server_port)
        mp.setenv(
            "DIRECT_CONNECTION_PROXY_ADDRESS", fake_direct_connection_proxy_address
        )
        main()

    with open(server_description_path) as server_description_file:
        server_description = json.load(server_description_file)

    assert server_description == expected_result
