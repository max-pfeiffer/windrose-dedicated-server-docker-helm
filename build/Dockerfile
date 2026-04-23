FROM steamcmd/steamcmd:debian-trixie AS install-stage

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates

RUN steamcmd +@sSteamCmdForcePlatformType windows +force_install_dir /srv/windrose +login anonymous +app_update 4129620 validate +quit

FROM debian:trixie-slim AS production-image

# Principle of least privilege: create a new user for running the application
RUN groupadd -g 10001 windrose && \
    useradd -r -u 10001 -g windrose --create-home windrose

# Install keyrings
RUN mkdir -pm755 /etc/apt/keyrings \
    && wget -O - https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key -

# Add sources file
RUN dpkg --add-architecture i386 \
    && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/trixie/winehq-trixie.sources

# Install Wine
RUN apt update \
    && apt install --install-recommends winehq-stable

WORKDIR /srv/windrose

RUN chown -R windrose:windrose /srv/valhwindroseeim

COPY --from=install-stage --chown=windrose:windrose /srv/windrose /srv/windrose

COPY --chown=windrose:windrose start.sh /srv/valheim/start.sh

# Use the unpriviledged user to run the application
USER 10001

ENTRYPOINT ["/srv/windrose/start.sh"]
