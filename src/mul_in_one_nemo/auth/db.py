"""Database access layer for FastAPI-Users."""

from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from mul_in_one_nemo.db import get_session_factory
from mul_in_one_nemo.db.models import OAuthAccount, User


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话（FastAPI依赖注入）."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """获取用户数据库访问器."""
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)
