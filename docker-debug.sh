#!/bin/bash
# Connect to remote Docker host for debugging
# Usage: ./docker-debug.sh <remote-host>

set -eo pipefail

if [ -z "$1" ]; then
    echo "Error: Must specify remote host"
    exit 1
fi

export DOCKER_HOST="$1"
echo "Connected to Docker daemon at $DOCKER_HOST"
docker info
docker ps -a
