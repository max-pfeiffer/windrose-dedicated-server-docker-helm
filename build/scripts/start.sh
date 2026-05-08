#!/bin/bash

SERVER_EXECUTABLE=/srv/windrose/R5/Binaries/Win64/WindroseServer-Win64-Shipping.exe
SERVER_DESCRIPTION=/srv/windrose/R5/ServerDescription.json
SERVER_LOGFILE=/srv/windrose/R5/Saved/Logs/R5.log
COUNTER=0

# When this image is run using the Helm chart, the Helm chart creates a file containing environment variables
# with server configuration. These environment variables are exported to the current shell if that file exists.
# The PASSWORD (and any other future secret fields) is provided directly via the container environment using
# `envFrom: secretRef`, so no secret file is sourced here.
if [[ -n "${CONFIG_FILE_PATH}" ]]; then
  if [[ -f "${CONFIG_FILE_PATH}" ]]; then
    set -a; source "${CONFIG_FILE_PATH}"; set +a
  else
    echo "CONFIG_FILE_PATH is set, but file with environment variables at ${CONFIG_FILE_PATH} does not exist"
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
