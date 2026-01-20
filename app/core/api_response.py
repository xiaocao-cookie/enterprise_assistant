from __future__ import annotations
from typing import Any

from pydantic import BaseModel
from fastapi import Response

from app.core.api_schemas import Meta
from app.core.http_consts import HDR_CACHE_CONTROL


# todo: 文档补充
def ok(data: Any, meta: dict[str, Any] | Meta | None = None) -> dict:
    """
    函数成功后返回的数据

    :param data: 数据
    :param meta: 元数据
    :return: 字典
    """
    if meta is None:
        return {"data": data}

    if isinstance(meta, Meta):
        return {"data": data, "meta": meta.model_dump()}

    if isinstance(meta, BaseModel):
        return {"data": data, "meta": meta.model_dump()}

    return {"data": data, "meta": dict(meta)}


def no_store(response: Response) -> None:
    """

    :param response:
    :return:
    """
    response.headers[HDR_CACHE_CONTROL] = "no-store"


def ok_no_store(
        response: Response,
        data: Any,
        meta: dict[str, Any] | Meta | None
) -> dict:
    """


    :param response:
    :param data:
    :param meta:
    :return:
    """
    no_store(response)
    return ok(data, meta=meta)
