from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    基于 sqlalchemy 的异步引擎 AsyncEngine 生成一个创建 AsyncSession 的工厂（async_sessionmaker）

    :param engine: SqlAlchemy 的异步数据库引擎
    :return: 生成异步 session 的工厂
    """
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)