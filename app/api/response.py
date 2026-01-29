from typing import Any

from fastapi import Response

from app.core.http_consts import HDR_CACHE_CONTROL
from app.core.api_response import ok


def no_store(response: Response) -> None:
    """
    不缓存此次的 response

    :param response: HTTP 的响应
    """
    response.headers[HDR_CACHE_CONTROL] = "no-store"


def ok_no_store(
        response: Response,
        data: Any,
        *,
        meta: Any | None = None
) -> dict:
    """
    对 response 响应正常返回但是不缓存数据

    :param response: HTTP 的响应
    :param data: 返回的业务数据
    :param meta: 返回的元数据
    """
    no_store(response)
    return ok(data, meta=meta)