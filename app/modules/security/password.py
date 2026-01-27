from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError


_ph = PasswordHasher()


def hash_password(raw: str) -> str:
    """
    将原始密码 raw 使用 argon2 的密码散列器加密

    :param raw: 原始密码
    :return: 加密后（散列后）的密码
    """
    return _ph.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    """
    验证原始密码 raw 与 加密后的 hashed 密码是否匹配

    :param raw: 原密码
    :param hashed: 散列后的密码
    :return: 如果匹配，则返回 True，否则返回 False
    """
    try:
        return _ph.verify(hashed, raw)
    except (VerifyMismatchError, VerificationError):
        return False