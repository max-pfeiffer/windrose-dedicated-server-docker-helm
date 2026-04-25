[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/max-pfeiffer/valheim-dedicated-server-docker-helm/graph/badge.svg?token=kP5LQLcpJi)](https://codecov.io/gh/max-pfeiffer/valheim-dedicated-server-docker-helm)

# Windrose Dedicated Server - Docker Image and Helm Chart
Start the Windrose server:
```shell
 docker run -it --user windrose --publish 28050:28050/tcp --publish 28050:28050/udp pfeiffermax/windrose-dedicated-server:latest
```

## Additional Information Sources
* [SteamDB](https://steamdb.info/app/4129620/info/)
* [Official Windrose Dedicated Server Guide](https://playwindrose.com/dedicated-server-guide)
* https://developer.valvesoftware.com/wiki/SteamCMD

## Other Game Server Projects
* [Rust dedicated server](https://github.com/max-pfeiffer/rust-game-server-docker)
* [Valheim dedicated server](https://github.com/max-pfeiffer/valheim-dedicated-server-docker-helm)