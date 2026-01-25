from typing import Any

from fastapi import Response

from app.core.http_consts import HDR_CACHE_CONTROL
from app.core.api_response import ok


def no_store(response: Response) -> None:
    """

    :param response:
    :return:
    """
    response.headers[HDR_CACHE_CONTROL] = "no-store"


def ok_no_store(
        response: Response,
        data: Any,
        meta: Any | None
) -> dict:
    """


    :param response:
    :param data:
    :param meta:
    :return:
    """
    no_store(response)
    return ok(data, meta=meta)