from __future__ import annotations

from fastapi import Request
from redis.asyncio import Redis


def get_redis(request: Request) -> Redis:
    """
    在 FastAPI 中，通过 Request 对象，从应用全局状态中取出已初始化好的 Redis 客户端

    :param request: HTTP 的请求
    :return: Redis 客户端
    """
    return request.app.state.redis