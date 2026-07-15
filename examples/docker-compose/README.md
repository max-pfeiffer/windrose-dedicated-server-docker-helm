# Simple Docker Compose example
This example contains a simple docker compose file for running the Windrose server on your machine (MacOS, Windows, Linux).

It demonstrates the usage of a [Docker Volume](https://docs.docker.com/storage/volumes/) to persist the Windrose server data.

Also check out [my guide for setting up a Windrose dedicated server with Docker and Docker Compose](https://max-pfeiffer.github.io/a-guide-for-setting-up-a-windrose-dedicated-server-using-docker-and-docker-compose.html).

## Usage
Clone the repo and start the Windrose server:
```shell
git clone https://github.com/max-pfeiffer/windrose-dedicated-server-docker-helm.git
cd windrose-dedicated-server-docker-helm/examples/docker-compose
docker compose up -d
```
Stop the server:
```shell
docker compose down
```
And show the logs, option `-f` follows the logs:
```shell
docker compose logs -f
```

## Automated Server Updates
When Kraken Express releases a Windrose update, you need to update your Windrose server as
well. So you need a new, updated Windrose dedicated server image.

As the docker compose file uses the `latest` tag for the Windrose server image, the only thing you need to do is
stopping/removing and creating/starting the container with docker compose. Docker then pulls the up-to-date Windrose
server image and starts the server. And you are done with your server update. :smiley: 

For instance, you can automate this with a cron job. Check out [windrose-server-update.sh](windrose-server-update.sh),
which is a simple script you can add as a daily job to your `/etc/crontab`. That way you ensure your server is always
up to date. 

## Transferring a local save game to the server
The compose stack shares the save-game volume (`windrose-save-dir`, mounted at `/srv/windrose/R5/Saved`) between the
Windrose server and a [file-manager](https://hub.docker.com/r/pfeiffermax/file-manager) web application, which serves
that directory on port 8080 without authentication (`FILES_ROOT: /srv/windrose/R5/Saved`, `AUTH_METHOD: none`). All
paths shown in the file manager are relative to `R5/Saved`.

Since game update 0.10.0.5.120, `RocksDB_v2` is the runtime save folder (the
[official guide](https://playwindrose.com/dedicated-server-guide/#wsg-faq-transfer) says "DO NOT TOUCH IT") and your
actual, transferable saves live in `RocksDB_v2_Backups`. The steps below cover this `RocksDB_v2_Backups` method for the
Steam game client.

1. **Shut both sides down.** Close the game client on your PC, and stop the server container (the official guide
   insists both are fully stopped before transferring):
   ```shell
   docker compose stop windrose-server   # file-manager keeps running
   ```
2. **Locate the save on your gaming PC.** Press Win+R and open:
   ```
   %localappdata%\R5\Saved\SaveProfiles\<YourSteamID>\RocksDB_v2_Backups\<GameVersion>\Worlds\
   ```
   Inside you find one folder per world backup, named by world ID. If there are several backups of the same world,
   take the `_Latest` one. Zip the entire world folder (right-click → "Compress to ZIP file") so the folder itself is
   inside the archive — do **not** rename it, the database relies on those IDs.
3. **Upload via the file manager.** Open `http://<your-docker-host>:8080` in a browser and navigate to:
   ```
   SaveProfiles/Default/RocksDB_v2_Backups/<GameVersion>/Worlds/
   ```
   Create any missing directories along the way. `<GameVersion>` (e.g. `0.10.0`) must match the server's version — you
   can check the existing directory name under `SaveProfiles/Default/RocksDB_v2/` for the exact value; client and
   server versions must match or the guide warns of bugs. Then drag-and-drop the zip into `Worlds/`, extract it there
   with the file manager's archive-extraction feature, and delete the zip. Verify the result is
   `Worlds/<WorldID>/<database files>`, not a double-nested folder.
4. **Fix file ownership.** The file-manager container runs as root, so the uploaded files are root-owned, while the
   game server runs as unprivileged UID 10001. Re-run the init container to chown the volume:
   ```shell
   docker compose up init-container
   ```
5. **Point the server at the world.** In [compose.yaml](compose.yaml), uncomment `WORLD_ISLAND_ID` and set it to the
   exact name of the folder you uploaded:
   ```yaml
   WORLD_ISLAND_ID: "<WorldID>"
   ```
   This is the containerized equivalent of the guide's "set `WorldIslandId` in `ServerDescription.json`" step — the
   container entrypoint writes it into that file on startup. The ID is also persisted on the volume, so the server
   keeps loading this world on future starts even if you later remove the variable.
6. **Start and verify:**
   ```shell
   docker compose up -d
   docker compose logs -f windrose-server
   ```

Related option: the image also supports `AUTO_LOAD_LATEST_BACKUP_IF_HAS_BROKEN: "true"`, which tells the server to
restore broken save files from backups on launch — useful insurance when working with transferred backups, but not
required by the guide's procedure.

