from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError

from app.modules.security.jwt_claims import (
    CLAIM_ISS,
    CLAIM_SUB,
    CLAIM_VER,
    CLAIM_IAT,
    CLAIM_TYP,
    CLAIM_EXP,
    TOKEN_TYPE_ACCESS
)


@dataclass(frozen=True)
class TokenPayload:
    """ JWT 的载荷 """
    user_id: int
    token_ver: int
    typ: str


def create_access_token(
        *,
        secret: str,
        issuer: str,
        alg: str,
        user_id: int,
        token_ver: int,
        minutes: int,
) -> str:
    """
    创建 JWT 访问者令牌，此令牌的类型为 access

    :param secret: 私钥
    :param issuer: 发布者
    :param alg: 算法
    :param user_id: 登录用户的 ID
    :param token_ver: 令牌的版本
    :param minutes: 过期时间，当前时间增加 minutes 分钟
    :return: JWT 令牌
    """
    now = datetime.now(timezone.utc)
    payload = {
        CLAIM_ISS: str(issuer),
        CLAIM_SUB: str(int(user_id)),
        CLAIM_VER: int(token_ver),
        CLAIM_TYP: TOKEN_TYPE_ACCESS,
        CLAIM_IAT: int(now.timestamp()),
        CLAIM_EXP: int((now + timedelta(minutes=int(minutes))).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=str(alg))


def _must_int(payload: dict[str, Any], k: str) -> int:
    """
    确保 JWT 的载荷 payload 中的 k 字段放的内容可以转换为 int

    :param payload: JWT 的载荷
    :param k: payload 中的某个键
    :return: payload 中键 k 对应的值（int 转换后）
    """
    v = payload.get(k)
    if v is None:
        raise ValueError("invalid_token_payload")
    try:
        return int(v)
    except Exception as e:
        raise ValueError("invalid_token_payload") from e


def decode_access_token(
        *,
        token: str,
        secret: str,
        issuer: str,
        alg: str,
        leeway_seconds: int = 30,
) -> TokenPayload:
    """
    将 JWT 的 token 解析为自定义的 TokenPayload 格式

    :param token: JWT 的令牌
    :param secret: 私钥
    :param issuer: 签发者
    :param alg: 加密算法
    :param leeway_seconds: 时间校验的容错空间（以秒为单位）
    :return: TokenPayload
    """
    try:
        options = {
            "verify_aud": False,
            "require_exp": True,
            "require_sub": True,
            "require_iss": True,
            "leeway": int(leeway_seconds),
        }
        payload = jwt.decode(
            token,
            secret,
            algorithms=[str(alg)],
            issuer=str(issuer),
            options=options,
        )
    except JWTError as e:
        raise ValueError("invalid_token") from e

    if not isinstance(payload, dict):
        raise ValueError("invalid_token_payload")

    if payload.get(CLAIM_TYP) != TOKEN_TYPE_ACCESS:
        raise ValueError("invalid_token_type")

    user_id = _must_int(payload, CLAIM_SUB)
    token_ver = _must_int(payload, CLAIM_VER)

    iat = payload.get(CLAIM_IAT)
    if not iat:
        raise ValueError("invalid_token_payload")

    return TokenPayload(user_id=int(user_id), token_ver=int(token_ver), typ=TOKEN_TYPE_ACCESS)

