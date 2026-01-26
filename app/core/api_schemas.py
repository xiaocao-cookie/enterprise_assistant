from __future__ import annotations
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Meta(BaseModel):
    """ 元数据的模型 """
    model_config = ConfigDict(extra="allow")


class ApiResponse(BaseModel, Generic[T]):
    """ API响应模型 """
    data: T
    meta: Meta | None = None


class Empty(BaseModel):
    """
    # todo: 这是干啥的
    """
    ok: bool = True


class ActionResult(BaseModel):
    """
    # todo: 这是干啥的
    """
    ok: bool = True


class ErrorInfo(BaseModel):
    """ 异常信息的模型 """
    code: str
    message: Any
    request_id: str
    meta: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """ 异常响应的模型 """
    error: ErrorInfo