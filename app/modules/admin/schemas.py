from __future__ import annotations

from pydantic import BaseModel, Field


class GrantRoleReq(BaseModel):
    """ 授予角色的请求模型 """
    user_id: int
    role_name: str = Field(min_length=1, max_length=64)
    scope_key: str = Field(min_length=1, max_length=128)


class GrantRoleData(BaseModel):
    """ 授予角色的数据模型 """
    granted: bool = True
    idempotent: bool


class RevokeRoleData(BaseModel):
    """ 撤销角色的数据模型 """
    ok: bool = True
    deleted: int
    idempotent: bool


class GrantRow(BaseModel):
    """ 授权的每一行 """
    user_id: int
    role_name: str
    scope_key: str
    created_by: int | None
    created_at: str


class ListGrantsResp(BaseModel):
    """ 授权列表的响应体模型 """
    items: list[GrantRow]
