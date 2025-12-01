#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "==> 停止后端服务..."
pkill -f "uvicorn.*mul_in_one_nemo" || true

echo "==> 删除 Milvus collections..."
./scripts/milvus_control.sh restart

echo "==> 重建 PostgreSQL 数据库..."
psql $DATABASE_URL -c "DROP DATABASE IF EXISTS mul_in_one WITH (FORCE);"
psql $DATABASE_URL -c "CREATE DATABASE mul_in_one;"

echo "==> 运行数据库迁移..."
alembic upgrade head

echo "==> 创建初始用户..."
uv run python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def create_initial_user():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/mul_in_one')
    async with engine.begin() as conn:
        await conn.execute(text('''
            INSERT INTO users (username, email, display_name, role)
            VALUES ('test', 'test@example.com', 'Test User', 'admin')
        '''))
        print('✓ 初始用户创建成功: username=test')
    await engine.dispose()

asyncio.run(create_initial_user())
"

echo ""
echo "✓ 数据库重建完成！"
echo ""
echo "现在可以："
echo "  1. 启动后端: ./scripts/start_backend.sh"
echo "  2. 访问 API: http://localhost:8000"
echo "  3. 使用 username=test 进行测试"
