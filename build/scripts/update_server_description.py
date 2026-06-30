"""Update Server Description."""

import json
import sys
import uuid
from argparse import ArgumentParser
from os import getenv
from pathlib import Path

DEFAULT_PERSISTENT_SERVER_ID_FILE = "/srv/windrose/R5/Saved/persistent_server_id"


def get_persistent_server_id() -> str:
    """Return a stable, unique PersistentServerId.

    The game expects a 32-character uppercase hexadecimal string, e.g.
    "1B80182E460F727CEA080C8EEBB1EA0A", and the id must be both unique per
    server and persistent across restarts (the invite code is resolved via
    this id by the connection service).

    The id is read from the data volume if it was persisted on a previous
    start, otherwise a new id is generated and persisted for future starts.

    :return:
    """
    id_file: Path = Path(
        getenv("PERSISTENT_SERVER_ID_FILE", DEFAULT_PERSISTENT_SERVER_ID_FILE)
    )
    if id_file.exists():
        return id_file.read_text().strip()

    persistent_server_id: str = uuid.uuid4().hex.upper()
    id_file.parent.mkdir(parents=True, exist_ok=True)
    id_file.write_text(persistent_server_id)
    return persistent_server_id


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

    server_description["ServerDescription_Persistent"]["PersistentServerId"] = (
        get_persistent_server_id()
    )

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
