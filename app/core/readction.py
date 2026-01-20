from __future__ import annotations

import re
from typing import Any


# 已编译的正则表达式
_RE_BEARER = re.compile(r"\bBearer\s+([A-Za-z0-9\-._~+/]+=*)", re.IGNORECASE)
_RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+=*\.[A-Za-z0-9_-]+=*\.[A-Za-z0-9_-]+=*\b")


# 敏感字段
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "jwt",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
}


def redact_str(s: str) -> str:
    """
    对字符串 s 进行脱敏处理

    :param s: 字符串，需匹配 Bearer 令牌和 JWT
    :return: 脱敏后的字符串
    """
    s = _RE_BEARER.sub("Bearer ***", s)

    s = _RE_JWT.sub("***.***.***", s)
    return s


def redact_obj(obj: Any) -> Any:
    """
    对任意 obj 进行脱敏处理

    :param obj: python 的任意对象
    :return: 脱敏后的结果

    具体描述：
        1. obj 为空： 返回 None
        2. obj 为 int,float,bool： 返回 obj 本身
        3. obj 为 list，tuple: 递归脱敏 obj 内部对象
        4. obj 为 dict：
            先判断键在不在敏感字段 SENSITIVE_KEYS 中，
                - 如果在，直接对其所对应的值进行脱敏处理（调用 redact_strs）
                - 如果不在，递归的对字典中的所有值进行脱敏处理（调用 redact_obj）
        5. 保底策略： 如果上述条件都不符合，原样返回 obj
    """
    if obj is None:
        return None

    if isinstance(obj, str):
        return redact_str(obj)

    if isinstance(obj, (int, float, bool)):
        return obj

    if isinstance(obj, list):
        return [redact_obj(x) for x in obj]

    if isinstance(obj, tuple):
        return tuple(redact_obj(x) for x in obj)

    if isinstance(obj, dict):
        out: dict[Any, Any] = {}
        for k, v in obj.items():
            kk = k
            if isinstance(kk, str):
                kl = kk.lower()

                if kl in SENSITIVE_KEYS:
                    out[kk] = "***"
                    continue
            out[kk] = redact_obj(v)

        return out

    return obj
