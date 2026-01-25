from __future__ import annotations
from typing import Any

from pydantic import BaseModel

from app.core.api_schemas import Meta


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

