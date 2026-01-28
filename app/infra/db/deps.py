from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    为每个 request 提供一个异步的 session（此 session 由 SqlAlchemy 提供）

    :param request: HTTP 的请求对象
    :return: 生成的 sqlalchemy.ext.asyncio 下的 AsyncSession 对象
    """
    session_maker = request.app.state.db_session_maker
    async with session_maker() as session:
        yield session
