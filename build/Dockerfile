FROM debian:trixie-slim AS install-stage

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates \
    lib32gcc-s1 \
    lib32stdc++6 \
    wget

WORKDIR /steam

RUN wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz && tar zxvf steamcmd_linux.tar.gz

RUN ./steamcmd.sh +login anonymous +quit
RUN ./steamcmd.sh +@sSteamCmdForcePlatformType windows +force_install_dir /srv/windrose +login anonymous +app_update 4129620 validate +quit

FROM debian:trixie-slim AS production-image

# Principle of least privilege: create a new user for running the application
RUN groupadd -g 10001 windrose && \
    useradd -r -u 10001 -g windrose -s /bin/bash --create-home windrose

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates \
    gnupg \
    wget \
    python3 \
    xvfb \
    xauth \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install keyrings
RUN mkdir -pm755 /etc/apt/keyrings \
    && wget -O - https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key -

# Add sources file
RUN dpkg --add-architecture i386 \
    && wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/trixie/winehq-trixie.sources

# Install Wine
RUN apt-get update \
    && apt-get install --install-recommends -y winehq-stable

WORKDIR /srv/windrose

RUN chown -R windrose:windrose /srv/windrose

COPY --from=install-stage --chown=windrose:windrose /srv/windrose /srv/windrose

COPY --chown=windrose:windrose start.sh /srv/windrose/start.sh

COPY --chown=windrose:windrose supdate_server_description.py /srv/windrose/update_server_description.py

RUN chmod +x /srv/windrose/start.sh

ENV WINEPREFIX=/home/windrose/.wine \
    WINEARCH=win64 \
    WINEDLLOVERRIDES="mscoree,mshtml=" \
    DISPLAY=:0

RUN Xvfb :0 -screen 0 1024x768x16 & \
    sleep 2 && \
    su -l windrose -c "WINEPREFIX=/home/steam/.wine WINEARCH=win64 WINEDLLOVERRIDES='mscoree,mshtml=' winecfg -v win10 >/dev/null 2>&1; wineboot --init >/dev/null 2>&1" && \
    kill %1 2>/dev/null; true \

# Use the unpriviledged user to run the application
USER 10001

#ENTRYPOINT ["/srv/windrose/start.sh"]

CMD /bin/bash
