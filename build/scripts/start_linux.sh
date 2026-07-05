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
    echo "CONFIG_FILE_PATH is set, but file with environment variables at ${CONFIG_FILE_PATH} does not exit"
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

echo "Modifying ServerDescription.json ..."
python3 update_server_description.py "$SERVER_DESCRIPTION"
echo "ServerDescription.json modified"

# Start the Windrose server eventually
echo "Starting the server ..."
UE_TRUE_SCRIPT_NAME=$(echo \"$0\" | xargs readlink -f)
UE_PROJECT_ROOT=$(dirname "$UE_TRUE_SCRIPT_NAME")
chmod +x "$UE_PROJECT_ROOT/R5/Binaries/Linux/WindroseServer-Linux-Shipping"
"$UE_PROJECT_ROOT/R5/Binaries/Linux/WindroseServer-Linux-Shipping" R5 "$@"