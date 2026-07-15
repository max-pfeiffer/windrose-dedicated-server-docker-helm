[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/max-pfeiffer/windrose-dedicated-server-docker-helm/graph/badge.svg?token=4xXsgY0nah)](https://codecov.io/gh/max-pfeiffer/windrose-dedicated-server-docker-helm)
[![Code Quality](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/code-quality.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/code-quality.yaml)
[![Test Image Build](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/test-image-build.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/test-image-build.yaml)
[![Publish Docker Image](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/publish.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/publish.yaml)
[![Lint Helm Chart](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/helm-lint.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/helm-lint.yaml)
[![Release Helm Charts](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/helm-release.yaml/badge.svg)](https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm/actions/workflows/helm-release.yaml)
![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/pfeiffermax/windrose-dedicated-server?sort=semver)
![Docker Pulls](https://img.shields.io/docker/pulls/pfeiffermax/windrose-dedicated-server)

# Windrose Dedicated Server - Docker Image and Helm Chart
This Docker image provides a [Windrose](https://playwindrose.com/) dedicated game server.
You will find here also a [Helm Chart](https://helm.sh/) for running a Windrose dedicated server on
[Kubernetes container orchestration system](https://kubernetes.io/).
This Windrose dedicated server is run with **Linux native binaries** on Debian Trixie.

My automation checks the [Windrose official Image build](https://hub.docker.com/r/windroseserver/windroseserver) every
night. If a new Image was published by Kraken Express, a new Docker image will be built
with this new version. Just use the `latest` tag and you will always have an up-to-date Docker image. No need to
manually run any server updates and mess around with your Docker image. It's that simple. :smiley:

Have a look at the [docker compose example](examples/docker-compose/compose.yaml) and
[its documentation](examples/docker-compose#automated-server-updates).
There you can see how a server update can be automated with a simple script.
Also check out [my guide for setting up a Windrose dedicated server with Docker and Docker Compose](https://max-pfeiffer.github.io/a-guide-for-setting-up-a-windrose-dedicated-server-using-docker-and-docker-compose.html). 
I also did an [in-depth analysis of the official Windrose Docker image](https://max-pfeiffer.github.io/kraken-express-published-an-official-windrose-dedicated-server-docker-image.html).

Please keep in mind that the Windrose server is currently still in development as the game is in early access state.
During the last weeks I already encountered some breaking changes for instance the directory of the world saves changed.
So expect further breaking changes. I also have to say that the Windrose server is a weird thing to operate in a
container. It was just not made for doing this. I had to implement quite some tricks to get it going.
And I hope Kraken Express will improve the server so it can be run in a container in a good way.  

**Docker Hub:** https://hub.docker.com/r/pfeiffermax/windrose-dedicated-server

**GitHub Repository:** https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm

## IMPORTANT CHANGE SINCE V2.0.0 (5.7.2026, Image Tag 0.10.0.7.33-372c3516)
Kraken Express published an [official Docker Image with Linux binaries](https://hub.docker.com/r/windroseserver/windroseserver)
just recently. So my image is using these Linux binaries from now on. Let's hope Kraken Express updates this image when
they publish a new Game client via Steam. I declared that as a breaking change as this might break something depending
on your setup.

## Usage
### Configuration
You can configure the Windrose server with the following environment variables:
* `INVITE_CODE` - invite code to find your server. 0-9, a-z and A-Z symbols are allowed. Should contain at least 6 symbols. Case sensitive.
* `PASSWORD` - this is the password.
* `SERVER_NAME` - name of your server. Helpful if invite codes look similar
* `MAX_PLAYER_COUNT` - maximum number of simultaneous players on your server.
* `USER_SELECTED_REGION` - specifies the region for the Connection Service. Supported options: SEA, CIS, EU
   (EU covers both EU & NA). If left empty, the server will automatically detect and select the optimal region based on
   latency. If desired region is specified (for example, EU), the server will use that region exclusively.
* `P2P_PROXY_ADDRESS` - IP Address for listening sockets.
* `USE_DIRECT_CONNECTION` - if true, the server will create sockets for direct connection with clients. If false, the server will use ICE protocol to establish P2P connection.
* `DIRECT_CONNECTION_SERVER_ADDRESS` - address for direct connection. For future purposes. Not used now.
* `DIRECT_CONNECTION_SERVER_PORT` - port for direct connection. Should be available for TCP and UDP connection if UseDirectConnection is true.
* `DIRECT_CONNECTION_PROXY_ADDRESS` - can be used to choose specified network on computer where server with direct connection is running. 0.0.0.0 should be used by default.
* `AUTO_LOAD_LATEST_BACKUP_IF_HAS_BROKEN` - if true, the server automatically loads the latest backup if the world save is broken.
* `WORLD_ISLAND_ID` - ID of the world the server should load. Only needed if you want to switch to another world,
   see [Importing a save game](#importing-a-save-game).

Use `--env` to set these variables in the Docker image.

As the Windrose server is running in the Docker container as a stateless application, you want to have all stateful server
data (config, saves, etc.) stored in a [Docker volume](https://docs.docker.com/storage/volumes/)
which is persisted **outside** the container. By default, the Windrose server stores that data in `/srv/windrose/R5/Saved`.
You need to make sure that this directory is mounted on a [Docker Volume](https://docs.docker.com/storage/volumes/).

The server needs a unique and stable `PersistentServerId` so that invite codes keep resolving to your server. On the
first start a new id is generated automatically and persisted to `/srv/windrose/R5/Saved/persistent_server_id` so it
survives container restarts. As long as you mount `/srv/windrose/R5/Saved` on a Docker Volume, you do not need to do
anything. If you want to store this id somewhere else, you can override its location with the optional
`PERSISTENT_SERVER_ID_FILE` environment variable.

### Docker Run
For testing purposes, you can fire up a Docker container like this:
```shell
docker run -it --publish 28050:28050/tcp --publish 28050:28050/udp --env SERVER_NAME=MyServer --env MAX_PLAYER_COUNT=5 pfeiffermax/windrose-dedicated-server:latest
```

### Docker Compose
Please have a look at the [docker compose example](examples/docker-compose/README.md). The docker compose example 
contains [a Web based file manager](https://github.com/max-pfeiffer/file-manager) for managing your save games in a very 
convenient way. There are very detailed instructions for 
[transferring a local save game to the server in the instructions](examples/docker-compose/README.md#transferring-a-local-save-game-to-the-server).

## Helm chart
If you would like to run the Windrose server in your [Kubernetes](https://kubernetes.io/) cluster, I provide a
[Helm chart](https://helm.sh/) you could use: [https://max-pfeiffer.github.io/windrose-dedicated-server-docker-helm](https://max-pfeiffer.github.io/windrose-dedicated-server-docker-helm)

There is also [documentation available](charts/windrose/README.md) for that Helm chart.

If you want to run your Windrose server on bare metal Kubernetes, check out
[my blog article](https://max-pfeiffer.github.io/hosting-game-servers-on-bare-metal-kubernetes-with-cilium-as-cni.html)
on how to do that using [Cilium](https://cilium.io/).

## Additional Information Sources
* [SteamDB](https://steamdb.info/app/4129620/info/)
* [Official Windrose Dedicated Server Guide](https://playwindrose.com/dedicated-server-guide)
* https://developer.valvesoftware.com/wiki/SteamCMD

## Other Game Server Projects
* [Rust dedicated server](https://github.com/max-pfeiffer/rust-game-server-docker)
* [Valheim dedicated server](https://github.com/max-pfeiffer/valheim-dedicated-server-docker-helm)