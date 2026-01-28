from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterReq(BaseModel):
    """ 注册的请求体模型 """
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginReq(BaseModel):
    """ 登录的请求体模型 """
    email: EmailStr
    password: str


class TokenResp(BaseModel):
    """ 令牌响应体模型 """
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    refresh_token: str


class RefreshReq(BaseModel):
    """ 刷新令牌的请求体模型 """
    refresh_token: str


class MeResp(BaseModel):
    """ 个人信息的响应体模型 """
    id: int
    email: EmailStr
    is_active: bool
    is_superadmin: bool