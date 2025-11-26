#!/usr/bin/env bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Assuming the script is in PROJECT_ROOT/scripts/, the project root is one level up
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set the path to the Milvus docker-compose file using the absolute path
MILVUS_COMPOSE_FILE="$PROJECT_ROOT/external/NeMo-Agent-Toolkit/examples/deploy/docker-compose.milvus.yml"

# Check if the file exists
if [ ! -f "$MILVUS_COMPOSE_FILE" ]; then
    echo "Error: Could not find the Milvus docker-compose file at: $MILVUS_COMPOSE_FILE"
    exit 1
fi

function show_help {
    echo "Usage: ./scripts/milvus_control.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start    Start the Milvus services in detached mode"
    echo "  stop     Stop and remove the Milvus containers"
    echo "  restart  Restart the Milvus services"
    echo "  status   Show the status of Milvus containers"
    echo "  logs     Follow the logs of Milvus containers"
}

if [ -z "$1" ]; then
    show_help
    exit 1
fi

case "$1" in
    start)
        echo "Starting Milvus services..."
        docker compose -f "$MILVUS_COMPOSE_FILE" up -d
        if [ $? -eq 0 ]; then
            echo "Milvus services started successfully."
        else
            echo "Failed to start Milvus services."
        fi
        ;;
    stop)
        echo "Stopping Milvus services..."
        docker compose -f "$MILVUS_COMPOSE_FILE" down
        ;;
    restart)
        echo "Restarting Milvus services..."
        docker compose -f "$MILVUS_COMPOSE_FILE" down && \
        docker compose -f "$MILVUS_COMPOSE_FILE" up -d
        ;;
    status)
        docker compose -f "$MILVUS_COMPOSE_FILE" ps
        ;;
    logs)
        docker compose -f "$MILVUS_COMPOSE_FILE" logs -f
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
