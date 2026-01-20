from __future__ import annotations
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

# todo: 文档补充
class Meta(BaseModel):
    """  """
    model_config = ConfigDict(extra="allow")


class ApiResponse(BaseModel, Generic[T]):
    """  """
    data: T
    meta: Meta | None = None


class Empty(BaseModel):
    """  """
    ok: bool = True


class ActionResult(BaseModel):
    """  """
    ok: bool = True


class ErrorInfo(BaseModel):
    """  """
    code: str
    message: Any
    request_id: str
    meta: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """  """
    error: ErrorInfo