from __future__ import annotations

import asyncio
from typing import Any, Awaitable

def run_async(coro: Awaitable[Any]) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None  # 如果没有，就设置loop变量为空
    if loop and loop.is_running():  #
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    return asyncio.run(coro)
