#!/usr/bin/env bash
set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

# Check if Milvus is running
check_milvus() {
    echo "Checking Milvus connection..."
    
    # Check if port 19530 is open
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost 19530 2>/dev/null; then
            echo "✓ Milvus is running on port 19530"
            return 0
        fi
    fi
    
    echo "⚠️  Warning: Cannot connect to Milvus on port 19530"
    echo "   The backend will fail to start without Milvus."
    echo ""
    echo "   To start Milvus, run:"
    echo "   ./scripts/milvus_control.sh start"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
}

check_milvus

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
