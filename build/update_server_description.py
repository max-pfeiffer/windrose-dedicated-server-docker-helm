import json
from argparse import ArgumentParser
from os import getenv
from pathlib import Path

def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("server_description", help="ServerDescription.json file path")
    args = parser.parse_args()

    server_description_file_path: Path = Path(args.server_description)
    if not server_description_file_path.exists():
        print(f"ServerDescription.json file does not exist: {server_description_file_path}")
        exit(1)

    with open(server_description_file_path) as server_description_file:
        server_description = json.load(server_description_file)

    invite_code: str = getenv("INVITE_CODE")
    password: str = getenv("PASSWORD")
    server_name: str = getenv("SERVER_NAME")
    max_player_count: int = int(getenv("MAX_PLAYER_COUNT"))
    user_selected_region: str = getenv("USER_SELECTED_REGION")
    p2p_proxy_address: str = getenv("P2P_PROXY_ADDRESS")
    use_direct_connection: bool = bool(getenv("USE_DIRECT_CONNECTION"))
    direct_connection_server_address: str = getenv("DIRECT_CONNECTION_SERVER_ADDRESS")
    direct_connection_server_port: int = int(getenv("DIRECT_CONNECTION_SERVER_PORT"))
    direct_connection_proxy_address: str = getenv("DIRECT_CONNECTION_PROXY_ADDRESS")

    if invite_code is not None:
        server_description["ServerDescription_Persistent"]["InviteCode"] = invite_code

    if password is None:
        server_description["ServerDescription_Persistent"]["IsPasswordProtected"] = False
        server_description["ServerDescription_Persistent"]["Password"] = ""
    else:
        server_description["ServerDescription_Persistent"]["IsPasswordProtected"] = True
        server_description["ServerDescription_Persistent"]["Password"] = password

    if server_name is not None:
        server_description["ServerDescription_Persistent"]["ServerName"] = server_name

    if max_player_count is not None:
        server_description["ServerDescription_Persistent"]["MaxPlayerCount"] = max_player_count

    if user_selected_region is not None:
        server_description["ServerDescription_Persistent"]["UserSelectedRegion"] = user_selected_region

    if p2p_proxy_address is not None:
        server_description["ServerDescription_Persistent"]["P2pProxyAddress"] = p2p_proxy_address

    if use_direct_connection:
        server_description["ServerDescription_Persistent"]["UseDirectConnection"] = use_direct_connection

    if direct_connection_server_address is not None:
        server_description["ServerDescription_Persistent"]["DirectConnectionServerAddress"] = direct_connection_server_address

    if direct_connection_server_port is not None:
        server_description["ServerDescription_Persistent"]["DirectConnectionServerPort"] = direct_connection_server_port

    if direct_connection_proxy_address is not None:
        server_description["ServerDescription_Persistent"]["DirectConnectionProxyAddress"] = direct_connection_proxy_address

    with open(server_description_file_path, "w") as server_description_file:
        json.dump(server_description, server_description_file)

if __name__ == "__main__":
    main()
