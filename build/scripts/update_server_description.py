"""Update Server Description."""

import json
import sys
import uuid
from argparse import ArgumentParser
from os import getenv
from pathlib import Path

DEFAULT_PERSISTENT_SERVER_ID_FILE = "/srv/windrose/R5/Saved/persistent_server_id"
DEFAULT_WORLD_ISLAND_ID_FILE = "/srv/windrose/R5/Saved/world_island_id"

TRUTHY_VALUES = ("1", "true", "yes", "on")


def get_bool_env(name: str) -> bool | None:
    """Parse a boolean environment variable.

    Environment variables are always strings, so a plain bool() cast would
    treat "false" or "0" as True.

    :param name:
    :return:
    """
    value: str | None = getenv(name)
    if value is None:
        return None
    return value.strip().lower() in TRUTHY_VALUES


def get_int_env(name: str) -> int | None:
    """Parse an integer environment variable.

    :param name:
    :return:
    """
    value: str | None = getenv(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        print(f"{name} must be an integer, got: {value}", file=sys.stderr)
        sys.exit(1)


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
        persisted_id: str = id_file.read_text().strip()
        # An empty file (e.g. from an interrupted write) must not result in an
        # empty PersistentServerId, so a new id is generated in that case.
        if persisted_id:
            return persisted_id

    persistent_server_id: str = uuid.uuid4().hex.upper()
    id_file.parent.mkdir(parents=True, exist_ok=True)
    id_file.write_text(persistent_server_id)
    return persistent_server_id


def get_world_island_id(current_worlds: list[str]) -> str | None:
    """Return the WorldIslandId of the world the server should load.

    The id is resolved in this order:

    1. WORLD_ISLAND_ID environment variable: lets the user switch to another
       world, e.g. an imported save game.
    2. The id persisted on the data volume from a previous start.
    3. The single existing world directory, if there is exactly one.

    The resolved id is persisted on the data volume, so the server keeps
    loading the same world on future starts even if additional worlds are
    imported later or the environment variable is removed. If no world exists
    yet, None is returned and the server generates a new world on startup.

    :param current_worlds:
    :return:
    """
    id_file: Path = Path(getenv("WORLD_ISLAND_ID_FILE", DEFAULT_WORLD_ISLAND_ID_FILE))

    # An empty file (e.g. from an interrupted write) is treated like a missing
    # file, so the world can still be resolved via the other sources.
    persisted_world_island_id: str | None = None
    if id_file.exists():
        persisted_world_island_id = id_file.read_text().strip() or None

    world_island_id: str | None = getenv("WORLD_ISLAND_ID")
    if world_island_id:
        if world_island_id not in current_worlds:
            print(
                f"World with WORLD_ISLAND_ID {world_island_id} does not exist. "
                f"Available worlds: {current_worlds}",
                file=sys.stderr,
            )
            sys.exit(1)
    elif persisted_world_island_id:
        world_island_id = persisted_world_island_id
        if world_island_id not in current_worlds:
            print(
                f"Persisted world {world_island_id} does not exist anymore. "
                f"Available worlds: {current_worlds}. "
                f"Set WORLD_ISLAND_ID to choose a world.",
                file=sys.stderr,
            )
            sys.exit(1)
    elif len(current_worlds) == 0:
        print("Windrose Server is generating a new world ID")
        return None
    elif len(current_worlds) == 1:
        world_island_id = current_worlds[0]
    else:
        print(
            f"Multiple worlds found, cannot determine the correct world. "
            f"Available worlds: {current_worlds}. "
            f"Set WORLD_ISLAND_ID to choose a world.",
            file=sys.stderr,
        )
        sys.exit(1)

    id_file.parent.mkdir(parents=True, exist_ok=True)
    id_file.write_text(world_island_id)
    return world_island_id


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
            f"{server_description_file_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(server_description_file_path) as server_description_file:
        server_description = json.load(server_description_file)

    current_worlds = get_current_worlds(get_game_version(server_description))

    server_description["ServerDescription_Persistent"]["PersistentServerId"] = (
        get_persistent_server_id()
    )

    invite_code: str | None = getenv("INVITE_CODE")
    password: str = getenv("PASSWORD", "")
    server_name: str | None = getenv("SERVER_NAME")
    max_player_count: int | None = get_int_env("MAX_PLAYER_COUNT")
    user_selected_region: str | None = getenv("USER_SELECTED_REGION")
    p2p_proxy_address: str | None = getenv("P2P_PROXY_ADDRESS")
    use_direct_connection: bool | None = get_bool_env("USE_DIRECT_CONNECTION")
    direct_connection_server_address: str | None = getenv(
        "DIRECT_CONNECTION_SERVER_ADDRESS"
    )
    direct_connection_server_port: int | None = get_int_env(
        "DIRECT_CONNECTION_SERVER_PORT"
    )
    direct_connection_proxy_address: str | None = getenv(
        "DIRECT_CONNECTION_PROXY_ADDRESS"
    )
    auto_load_latest_backup_if_has_broken: bool | None = get_bool_env(
        "AUTO_LOAD_LATEST_BACKUP_IF_HAS_BROKEN"
    )

    world_island_id: str | None = get_world_island_id(current_worlds)
    if world_island_id is not None:
        server_description["ServerDescription_Persistent"]["WorldIslandId"] = (
            world_island_id
        )

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

    if use_direct_connection is not None:
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

    if auto_load_latest_backup_if_has_broken is not None:
        server_description["ServerDescription_Persistent"][
            "AutoLoadLatestBackupIfHasBroken"
        ] = auto_load_latest_backup_if_has_broken

    # The container runs exactly one server instance per data volume, so
    # launching multiple instances from the same installation must stay
    # disabled.
    server_description["ServerDescription_Persistent"][
        "CanLaunchMultipleServerInstances"
    ] = False

    with open(server_description_file_path, "w") as server_description_file:
        json.dump(server_description, server_description_file)


if __name__ == "__main__":
    main()
