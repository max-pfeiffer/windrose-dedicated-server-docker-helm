# Windrose Dedicated Server - Docker Image and Helm Chart
Start the Windrose server:
```shell
 docker run -it --user windrose --publish 28050:28050/tcp --publish 28050:28050/udp windrose:test
```

## Additional Information Sources
* [SteamDB](https://steamdb.info/app/4129620/info/)
* [Official Windrose Dedicated Server Guide](https://playwindrose.com/dedicated-server-guide)
* https://developer.valvesoftware.com/wiki/SteamCMD

## Other Game Server Projects
* [Rust dedicated server](https://github.com/max-pfeiffer/rust-game-server-docker)
* [Valheim dedicated server](https://github.com/max-pfeiffer/valheim-dedicated-server-docker-helm)