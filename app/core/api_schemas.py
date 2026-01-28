from __future__ import annotations
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Meta(BaseModel):
    """ 元数据的模型 """
    model_config = ConfigDict(extra="allow")


class ApiResponse(BaseModel, Generic[T]):
    """ 带范型的 API响应模型 """
    data: T
    meta: Meta | None = None


class Empty(BaseModel):
    """ 空占位模型，用来适配无需返回业务数据的接口 """
    ok: bool = True


class ActionResult(BaseModel):
    """ 表示某个操作是否成功 """
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