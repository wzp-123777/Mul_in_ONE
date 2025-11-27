#!/usr/bin/env bash
set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

echo "Starting FastAPI backend server..."
echo "API will be available at: http://localhost:8000"
echo ""

# Start uvicorn with reload, excluding problematic directories
uv run uvicorn mul_in_one_nemo.service.app:create_app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 \
  --reload-exclude "external/*" \
  --reload-exclude ".postgresql/*" \
  --reload-exclude ".milvus/*" \
  --reload-exclude "node_modules/*" \
  --reload-exclude ".venv/*"
