#!/usr/bin/env bash

# Mul-in-ONE Diagnostic Script
# Checks system dependencies, services, and common issues

set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Mul-in-ONE Diagnostic Report"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Check environment variables
echo "1. Environment Variables"
echo "------------------------"

if [ -f "$PROJECT_ROOT/.envrc" ]; then
    print_ok ".envrc file exists"
    
    # Check critical variables
    source "$PROJECT_ROOT/.envrc" 2>/dev/null || true
    
    if [ -n "${DOCKER_VOLUME_DIRECTORY:-}" ]; then
        print_ok "DOCKER_VOLUME_DIRECTORY is set: $DOCKER_VOLUME_DIRECTORY"
    else
        print_error "DOCKER_VOLUME_DIRECTORY is not set"
    fi
    
    if [ -n "${MILVUS_CONFIG_DIR:-}" ]; then
        print_ok "MILVUS_CONFIG_DIR is set: $MILVUS_CONFIG_DIR"
    else
        print_warn "MILVUS_CONFIG_DIR is not set (using default)"
    fi
    
    if [ -n "${DATABASE_URL:-}" ]; then
        print_ok "DATABASE_URL is set"
    else
        print_error "DATABASE_URL is not set"
    fi
else
    print_error ".envrc file not found"
    echo "   Run: cp .envrc.example .envrc"
fi

echo ""

# 2. Check Milvus config issues
echo "2. Milvus Configuration"
echo "------------------------"

MILVUS_CONFIG_PATH="$PROJECT_ROOT/configs/milvus.yaml"
if [ -d "$MILVUS_CONFIG_PATH" ]; then
    print_error "milvus.yaml exists as a directory (should be removed)"
    echo "   Run: rmdir $MILVUS_CONFIG_PATH"
elif [ -f "$MILVUS_CONFIG_PATH" ]; then
    print_ok "milvus.yaml file exists"
else
    print_ok "No milvus.yaml (using Milvus defaults)"
fi

# Check docker-compose file
COMPOSE_FILE="$PROJECT_ROOT/configs/docker-compose.milvus.local.yml"
if [ -f "$COMPOSE_FILE" ]; then
    print_ok "docker-compose.milvus.local.yml exists"
    
    # Check if it has the problematic --config flag
    if grep -q -- '--config' "$COMPOSE_FILE" 2>/dev/null; then
        print_warn "docker-compose file contains --config flag (may cause issues)"
        echo "   The --config flag should be removed if milvus.yaml doesn't exist"
    else
        print_ok "docker-compose file does not use --config flag"
    fi
else
    print_error "docker-compose.milvus.local.yml not found"
fi

echo ""

# 3. Check Docker services
echo "3. Docker Services"
echo "------------------------"

if command -v docker >/dev/null 2>&1; then
    print_ok "Docker is installed"
    
    # Check if Docker daemon is running
    if docker info >/dev/null 2>&1; then
        print_ok "Docker daemon is running"
        
        # Check Milvus containers
        if docker ps --filter "name=milvus-standalone" --format "{{.Names}}" | grep -q "milvus-standalone"; then
            STATUS=$(docker ps --filter "name=milvus-standalone" --format "{{.Status}}")
            print_ok "milvus-standalone is running ($STATUS)"
            
            # Check memory allocation
            MEM_BYTES=$(docker inspect milvus-standalone --format='{{.HostConfig.Memory}}' 2>/dev/null || echo "0")
            if [ "$MEM_BYTES" -gt 0 ]; then
                MEM_GB=$((MEM_BYTES / 1073741824))
                if [ "$MEM_GB" -ge 8 ]; then
                    print_ok "Milvus memory limit: ${MEM_GB}GB (sufficient)"
                elif [ "$MEM_GB" -ge 4 ]; then
                    print_warn "Milvus memory limit: ${MEM_GB}GB (may cause OOM, recommend 8GB+)"
                else
                    print_error "Milvus memory limit: ${MEM_GB}GB (too low, will cause OOM)"
                    echo "   Set MILVUS_MEM_LIMIT=8g in .envrc and restart"
                fi
            fi
        else
            if docker ps -a --filter "name=milvus-standalone" --format "{{.Names}}" | grep -q "milvus-standalone"; then
                STATUS=$(docker ps -a --filter "name=milvus-standalone" --format "{{.Status}}")
                print_error "milvus-standalone exists but not running ($STATUS)"
                
                # Check for OOM in logs
                if docker logs milvus-standalone 2>&1 | grep -q "OOM\|Out of memory"; then
                    print_error "Milvus crashed due to OOM (Out of Memory)"
                    echo "   Increase MILVUS_MEM_LIMIT in .envrc to 8g or higher"
                fi
                
                echo "   Run: ./scripts/milvus_control.sh restart"
            else
                print_warn "milvus-standalone container not found"
                echo "   Run: ./scripts/milvus_control.sh start"
            fi
        fi
        
        # Check other services
        for service in milvus-etcd milvus-minio; do
            if docker ps --filter "name=$service" --format "{{.Names}}" | grep -q "$service"; then
                print_ok "$service is running"
            else
                print_warn "$service is not running"
            fi
        done
    else
        print_error "Docker daemon is not running"
        echo "   Start Docker Desktop or docker service"
    fi
else
    print_error "Docker is not installed"
fi

echo ""

# 4. Check port availability
echo "4. Port Availability"
echo "------------------------"

check_port() {
    local port=$1
    local service=$2
    
    if command -v nc >/dev/null 2>&1; then
        if nc -z localhost "$port" 2>/dev/null; then
            print_ok "$service port $port is accessible"
        else
            print_error "$service port $port is not accessible"
            echo "   Check if the service is running"
        fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -i :"$port" >/dev/null 2>&1; then
            print_ok "$service port $port is in use"
        else
            print_error "$service port $port is not in use"
        fi
    else
        print_warn "Cannot check port $port (nc or lsof not available)"
    fi
}

check_port 19530 "Milvus"
check_port 5432 "PostgreSQL"
check_port 8000 "Backend API"

echo ""

# 5. Check Python environment
echo "5. Python Environment"
echo "------------------------"

if command -v uv >/dev/null 2>&1; then
    print_ok "uv is installed"
else
    print_error "uv is not installed"
    echo "   Visit: https://github.com/astral-sh/uv"
fi

if [ -d "$PROJECT_ROOT/.venv" ]; then
    print_ok "Virtual environment exists"
else
    print_warn "Virtual environment not found"
    echo "   Run: uv venv"
fi

echo ""

# 6. Summary
echo "=========================================="
echo "Diagnostic Summary"
echo "=========================================="
echo ""
echo "Common fixes:"
echo ""
echo "1. If Milvus won't start or has OOM errors:"
echo "   # Increase memory limit to 8GB in .envrc:"
echo "   export MILVUS_MEM_LIMIT=\"8g\""
echo "   direnv allow  # or: source .envrc"
echo "   ./scripts/milvus_control.sh restart"
echo ""
echo "2. If environment variables are missing:"
echo "   cp .envrc.example .envrc"
echo "   direnv allow  # or: source .envrc"
echo ""
echo "3. If milvus.yaml is a directory:"
echo "   rmdir $PROJECT_ROOT/configs/milvus.yaml"
echo ""
echo "4. If backend can't connect to Milvus:"
echo "   nc -zv localhost 19530  # Test connection"
echo "   docker logs milvus-standalone --tail=100  # Check logs"
echo "   docker logs milvus-standalone 2>&1 | grep OOM  # Check for memory errors"
echo ""
