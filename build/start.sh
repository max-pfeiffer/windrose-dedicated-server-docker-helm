#!/bin/bash

SERVER_EXECUTABLE=/srv/windrose/R5/Binaries/Win64/WindroseServer-Win64-Shipping.exe
SERVER_DESCRIPTION=/srv/windrose/R5/ServerDescription.json
COUNTER=0

echo "Starting Windrose Dedicated Server"
if [ ! -f "$SERVER_DESCRIPTION" ]; then
  echo "Creating ServerDescription.json ..."
  xvfb-run --auto-servernum wine "$SERVER_EXECUTABLE" -log -STDOUT >/dev/null 2>&1 &
  RUN_PID=$!

  while [ ! -f "$SERVER_DESCRIPTION" ] && [ $COUNTER -lt 120 ]; do
      sleep 1
      COUNTER=$((COUNTER + 1))
  done

  if [ ! -f "$SERVER_DESCRIPTION" ]; then
    echo "Error: Failed to generate ServerDescription.json"
    kill "$RUN_PID" 2>/dev/null
    wait "$RUN_PID" 2>/dev/null
    wineserver -k 2>/dev/null
    exit 1
  fi

  kill "$RUN_PID" 2>/dev/null
  wait "$RUN_PID" 2>/dev/null
  wineserver -k 2>/dev/null
  sleep 2
  echo "ServerDescription.json created"
fi

echo "Starting the server ..."
xvfb-run --auto-servernum wine "$SERVER_EXECUTABLE" -log
