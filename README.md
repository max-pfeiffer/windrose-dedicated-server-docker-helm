[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/max-pfeiffer/windrose-dedicated-server-docker-helm/graph/badge.svg?token=4xXsgY0nah)](https://codecov.io/gh/max-pfeiffer/windrose-dedicated-server-docker-helm)
[![Code Quality](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/code-quality.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/code-quality.yaml)
[![Test Image Build](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/test-image-build.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/test-image-build.yaml)
[![Publish Docker Image](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/publish.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/publish.yaml)
![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/pfeiffermax/windrose-dedicated-server?sort=semver)
![Docker Pulls](https://img.shields.io/docker/pulls/pfeiffermax/windrose-dedicated-server)

# Windrose Dedicated Server - Docker Image and Helm Chart
This Docker image provides a [Windrose](https://playwindrose.com/) dedicated game server.
You will find here also a [Helm Chart](https://helm.sh/) for running a Windrose dedicated server on [Kubernetes container orchestration system](https://kubernetes.io/).

My automation checks the [Windrose public branch](https://steamdb.info/app/4129620/depots/?branch=public) every
night. If a new release was published by Kraken Express, a new Docker image will be built
with this new version. Just use the `latest` tag and you will always have an up-to-date Docker image. No need to
manually run any server updates and mess around with your Docker image. It's that simple. :smiley:

Have a look at the [docker compose example](examples/docker-compose/compose.yaml) and
[its documentation](examples/docker-compose#automated-server-updates).
There you can see how a server update can be automated with a simple script.

**Docker Hub:** https://hub.docker.com/r/pfeiffermax/windrose-dedicated-server

**GitHub Repository:** https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm

## Usage
### Configuration
You can configure the Windrose server with the following environment variables:
* `INVITE_CODE`- invite code to find your server. 0-9, a-z and A-Z symbols are allowed. Should contain at least 6 symbols. Case sensitive.
* `PASSWORD` - this is the password.
* `SERVER_NAME` - name of your server. Helpful if invite codes look similar
* `MAX_PLAYER_COUNT` - maximum number of simultaneous players on your server.
* `USER_SELECTED_REGION`- specifies the region for the Connection Service. Supported options: SEA, CIS, EU
   (EU covers both EU & NA). If left empty, the server will automatically detect and select the optimal region based on
   latency. If desired region is specified (for example, EU), the server will use that region exclusively.
* `P2P_PROXY_ADDRESS` - IP Address for listening sockets.
* `USE_DIRECT_CONNECTION` - if true, the server will create sockets for direct connection with clients. If false, the server will use ICE protocol to establish P2P connection.
* `DIRECT_CONNECTION_SERVER_ADDRESS` - address for direct connection. For future purposes. Not used now.
* `DIRECT_CONNECTION_SERVER_PORT` - port for direct connection. Should be available for TCP and UDP connection if UseDirectConnection is true.
* `DIRECT_CONNECTION_PROXY_ADDRESS` - сan be used to choose specified network on computer where server with direct connection is running. 0.0.0.0 should be used by default.

Use `--env` to set these variables in the Docker image.

As the Windrose server is running in the Docker container as a stateless application, you want to have all stateful server
data (config, saves, etc.) stored in a [Docker volume](https://docs.docker.com/storage/volumes/)
which is persisted **outside** the container. By default, the Windrose server stores that data in `/srv/windrose/R5/Saved`.
You need to make sure that this directory is mounted on a [Docker Volume](https://docs.docker.com/storage/volumes/).

### Docker Run
For testing purposes, you can fire up a Docker container like this:
```shell
docker run -it --publish 28050:28050/tcp --publish 28050:28050/udp --env SERVER_NAME=MyServer --env MAX_PLAYER_COUNT=5 pfeiffermax/windrose-dedicated-server:latest
```

### Docker Compose
Please have a look at the [docker compose example](examples/docker-compose/README.md).

## Additional Information Sources
* [SteamDB](https://steamdb.info/app/4129620/info/)
* [Official Windrose Dedicated Server Guide](https://playwindrose.com/dedicated-server-guide)
* https://developer.valvesoftware.com/wiki/SteamCMD

## Other Game Server Projects
* [Rust dedicated server](https://github.com/max-pfeiffer/rust-game-server-docker)
* [Valheim dedicated server](https://github.com/max-pfeiffer/valheim-dedicated-server-docker-helm)