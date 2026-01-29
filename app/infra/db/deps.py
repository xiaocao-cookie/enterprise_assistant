from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.request_context import get_workspace_id


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    为每个 request 提供一个异步的 session（此 session 由 SqlAlchemy 提供）

    :param request: HTTP 的请求对象
    :return: 生成的 sqlalchemy.ext.asyncio 下的 AsyncSession 对象
    """
    session_maker = request.app.state.db_session_maker

    async with session_maker.begin() as session:
        wid = getattr(request.state, "workspace_id", None)

        if wid is None:
            wid = get_workspace_id()
        wid_val = str(int(wid)) if wid else "0"

        await session.execute(
            text("SELECT set_config('app.tenant_id', :v, true)"),
            {"v": wid_val},
        )
        yield session