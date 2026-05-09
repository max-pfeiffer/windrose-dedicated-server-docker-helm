"""Update Server Descriptiin."""

import json
import sys
from argparse import ArgumentParser
from os import getenv
from pathlib import Path


def parse_args(args: list[str]):
    """Parse command line arguments.

    :param args:
    :return:
    """
    parser = ArgumentParser()
    parser.add_argument("server_description", help="ServerDescription.json file path")
    parsed_args = parser.parse_args(args)
    return parsed_args


def get_game_version(server_description: dict) -> str:
    """Extract game version from ServerDescription.json file.

    :param server_description:
    :return:
    """
    deployment_id = server_description["DeploymentId"]
    parts = deployment_id.split(".")
    version = ".".join(parts[:3])
    return version


def get_current_worlds(game_version: str) -> list[str]:
    """Aquire all world directories from file system.

    :param game_version:
    :return:
    """
    dir_names = []
    worlds_path = (
        Path("/srv/windrose/R5/Saved/SaveProfiles/Default/RocksDB_v2")
        / game_version
        / "Worlds"
    )
    if worlds_path.exists():
        dir_names = [p.name for p in worlds_path.iterdir() if p.is_dir()]
    return dir_names


def main() -> None:
    """Execute main functionality.

    :return:
    """
    args = parse_args(sys.argv[1:])

    server_description_file_path: Path = Path(args.server_description)
    if not server_description_file_path.exists():
        print(
            f"ServerDescription.json file does not exist: "
            f"{server_description_file_path}"
        )
        exit(1)

    with open(server_description_file_path) as server_description_file:
        server_description = json.load(server_description_file)

    current_worlds = get_current_worlds(get_game_version(server_description))

    invite_code: str | None = getenv("INVITE_CODE")
    password: str = getenv("PASSWORD", "")
    server_name: str | None = getenv("SERVER_NAME")
    max_player_count: int | None = (
        None
        if (getenv("MAX_PLAYER_COUNT") is None)
        else int(getenv("MAX_PLAYER_COUNT"))
    )
    user_selected_region: str | None = getenv("USER_SELECTED_REGION")
    p2p_proxy_address: str | None = getenv("P2P_PROXY_ADDRESS")
    use_direct_connection: bool = bool(getenv("USE_DIRECT_CONNECTION"))
    direct_connection_server_address: str | None = getenv(
        "DIRECT_CONNECTION_SERVER_ADDRESS"
    )
    direct_connection_server_port: int | None = (
        None
        if (getenv("DIRECT_CONNECTION_SERVER_PORT") is None)
        else int(getenv("DIRECT_CONNECTION_SERVER_PORT"))
    )
    direct_connection_proxy_address: str | None = getenv(
        "DIRECT_CONNECTION_PROXY_ADDRESS"
    )

    if len(current_worlds) == 0:
        print("Windrose Server is generating a new world ID")
    elif len(current_worlds) == 1:
        server_description["ServerDescription_Persistent"]["WorldIslandId"] = (
            current_worlds[0]
        )
    else:
        print("Multiple worlds found, cannot determine the correct world")
        exit(1)

    if invite_code is not None:
        server_description["ServerDescription_Persistent"]["InviteCode"] = invite_code

    if password == "":
        server_description["ServerDescription_Persistent"]["IsPasswordProtected"] = (
            False
        )
        server_description["ServerDescription_Persistent"]["Password"] = ""
    else:
        server_description["ServerDescription_Persistent"]["IsPasswordProtected"] = True
        server_description["ServerDescription_Persistent"]["Password"] = password

    if server_name is not None:
        server_description["ServerDescription_Persistent"]["ServerName"] = server_name

    if max_player_count is not None:
        server_description["ServerDescription_Persistent"]["MaxPlayerCount"] = (
            max_player_count
        )

    if user_selected_region is not None:
        server_description["ServerDescription_Persistent"]["UserSelectedRegion"] = (
            user_selected_region
        )

    if p2p_proxy_address is not None:
        server_description["ServerDescription_Persistent"]["P2pProxyAddress"] = (
            p2p_proxy_address
        )

    if use_direct_connection:
        server_description["ServerDescription_Persistent"]["UseDirectConnection"] = (
            use_direct_connection
        )

    if direct_connection_server_address is not None:
        server_description["ServerDescription_Persistent"][
            "DirectConnectionServerAddress"
        ] = direct_connection_server_address

    if direct_connection_server_port is not None:
        server_description["ServerDescription_Persistent"][
            "DirectConnectionServerPort"
        ] = direct_connection_server_port

    if direct_connection_proxy_address is not None:
        server_description["ServerDescription_Persistent"][
            "DirectConnectionProxyAddress"
        ] = direct_connection_proxy_address

    with open(server_description_file_path, "w") as server_description_file:
        json.dump(server_description, server_description_file)


if __name__ == "__main__":
    main()
