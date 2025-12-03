import asyncio
import asyncpg
import os
import sys

async def check_db():
    url = os.environ.get("DATABASE_URL", "postgresql://postgres@localhost:5432/postgres")
    # Adjust url to connect to 'postgres' db to check connection and create target db
    base_url = url.rsplit("/", 1)[0] + "/postgres"
    
    print(f"Attempting to connect to: {base_url}")
    try:
        conn = await asyncpg.connect(base_url)
        print("Successfully connected to PostgreSQL!")
        
        # Check if mul_in_one exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'mul_in_one'")
        if not exists:
            print("Database 'mul_in_one' does not exist. Creating...")
            await conn.execute("CREATE DATABASE mul_in_one")
            print("Database 'mul_in_one' created.")
        else:
            print("Database 'mul_in_one' already exists.")
            
        await conn.close()
        return True
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(check_db())
    except ImportError:
        print("asyncpg not installed.")
