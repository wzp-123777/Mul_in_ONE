#!/bin/bash
set -e

cd "$(dirname "$0")/.."


echo "==> 完全重建 PostgreSQL 数据库..."
rm -rf .postgresql/data
mkdir -p .postgresql/data .postgresql/run

echo "==> 停止后端服务..."
pkill -f "uvicorn.*mul_in_one_nemo" || true

echo "==> 删除 Milvus collections..."
./scripts/milvus_control.sh restart

echo "==> 停止 PostgreSQL..."
pg_ctl stop -D .postgresql/data -m fast 2>/dev/null || true
sleep 1

# 检查端口是否被占用
if lsof -i :5432 >/dev/null 2>&1; then
    echo "==> 端口 5432 被占用，正在终止进程..."
    PID=$(lsof -t -i :5432)
    kill -TERM $PID 2>/dev/null || true
    sleep 2
fi

echo "==> 初始化 PostgreSQL..."
initdb -D .postgresql/data

echo "==> 启动 PostgreSQL..."
pg_ctl start -D .postgresql/data -o "-k $PWD/.postgresql/run" -l .postgresql/data/postgres.log
sleep 2

echo "==> 创建数据库..."
psql -h localhost -p 5432 -d postgres -c "CREATE DATABASE mul_in_one;" || echo "数据库可能已存在"

echo "==> 创建 postgres 用户（如不存在）..."
psql -h localhost -p 5432 -d postgres -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'postgres'; END IF; END \$\$;" || echo "postgres 用户可能已存在"

echo "==> 运行数据库迁移..."
uv run alembic upgrade head

echo ""
echo "✓ 数据库重建完成！"
echo ""
