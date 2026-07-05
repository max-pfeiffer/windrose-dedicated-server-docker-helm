# Podman compose for the official Windrose server image

Runs the [official Windrose dedicated server image](https://hub.docker.com/r/windroseserver/windroseserver)
(`windroseserver/windroseserver`, published by Kraken Express) on a remote
Podman host with `podman compose`, driven from your local machine. The image
is a native Linux (Unreal Engine) server build, linux/amd64 only.

Unlike the image built by this repository, the official image has no
entrypoint logic and no environment variable handling: the server reads its
configuration exclusively from `R5/ServerDescription.json`, which is shipped
empty in the image. This example works around that:

- The `init-container` service seeds `ServerDescription.json` (with a
  generated `PersistentServerId`) on the save volume on first start and
  chowns the volume to the unprivileged container user `ue_user` (UID 1000).
- The `windrose-server` service symlinks the baked-in
  `/home/ue_user/app/R5/ServerDescription.json` to the seeded copy on the
  save volume before starting the server, so the server identity survives
  container recreation. A symlink is used instead of a file bind mount
  because bind mount sources resolve on the remote host when composing over
  a remote connection.

On first start the server writes back through the symlink and fills in the
missing fields (`DeploymentId`, `InviteCode`, `WorldIslandId`) while keeping
the seeded `PersistentServerId`.

To change the server settings, either edit the seed JSON in `compose.yaml`
and delete the file from the volume (or the whole volume) to re-seed it, or
edit the file on the volume directly and restart the server:

```shell
podman --connection remotebuilder exec -it windrose-official-image-server \
    vi /home/ue_user/app/R5/Saved/ServerDescription.json
```

## Prerequisites

- A Podman [system connection](https://docs.podman.io/en/latest/markdown/podman-system-connection.html)
  to a linux/amd64 host (called `remotebuilder` below):
  `podman system connection list`
- A compose provider installed locally, see the
  [remote builder example](../podman-compose-remote-builder/README.md) for
  the extra ssh and `podman-docker` host setup required by the
  `docker-compose` provider.

## Usage

```shell
cd examples/podman-compose-official-image
podman --connection remotebuilder compose up -d
podman --connection remotebuilder compose logs -f windrose-server
```

The first startup generates the world and takes a few minutes. The ports are
published on the remote host, so connect the game client to
`<remote host>:7777`.

Tear down with:

```shell
podman --connection remotebuilder compose down       # add -v to also delete the save volume
```
