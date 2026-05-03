#!/bin/bash

SERVER_EXECUTABLE=/srv/windrose/R5/Binaries/Win64/WindroseServer-Win64-Shipping.exe
SERVER_DESCRIPTION=/srv/windrose/R5/ServerDescription.json
SERVER_LOGFILE=/srv/windrose/R5/Saved/Logs/R5.log
COUNTER=0

# When this image is run using the Helm chart, the Helm chart creates files containing environment variables
# with server configuration and the password. These environment variables are exported to the current shell
# if those files exist.
if [[ -n "${CONFIG_FILE_PATH}" ]]; then
  if [[ -f "${CONFIG_FILE_PATH}" ]]; then
    set -a; source "${CONFIG_FILE_PATH}"; set +a
  else
    echo "SECRET_FILE_PATH is set, but file with environment variables at ${CONFIG_FILE_PATH} does not exit"
    exit 1
  fi
fi

if [[ -n "${SECRET_FILE_PATH}" ]]; then
  if [[ -f "${SECRET_FILE_PATH}" ]]; then
    set -a; source "${SECRET_FILE_PATH}"; set +a
  else
    echo "SECRET_FILE_PATH is set, but file with environment variables at ${SECRET_FILE_PATH} does not exit"
    exit 1
  fi
fi

echo "Starting Windrose Dedicated Server"

# Generate and modify ServerDescription.json file
if [[ ! -f "$SERVER_DESCRIPTION" ]]; then
  echo "Creating ServerDescription.json ..."
  xvfb-run --auto-servernum wine "$SERVER_EXECUTABLE" -log -STDOUT >/dev/null 2>&1 &
  RUN_PID=$!

  while [[ ! -f "$SERVER_DESCRIPTION" ]] && [[ $COUNTER -lt 120 ]]; do
      sleep 1
      COUNTER=$((COUNTER + 1))
  done

  if [[ ! -f "$SERVER_DESCRIPTION" ]]; then
    echo "Error: Failed to generate ServerDescription.json"
    kill "$RUN_PID"
    wait "$RUN_PID"
    wineserver -k
    exit 1
  fi

  kill "$RUN_PID"
  wait "$RUN_PID"
  wineserver -k
  sleep 2
  echo "ServerDescription.json created"
fi

echo "Modifying ServerDescription.json ..."
python3 update_server_description.py "$SERVER_DESCRIPTION"
echo "ServerDescription.json modified"

# Start the Windrose server eventually
echo "Starting the server ..."
xvfb-run --auto-servernum wine "$SERVER_EXECUTABLE" >/dev/null 2>&1 &

tail -f "$SERVER_LOGFILE"
