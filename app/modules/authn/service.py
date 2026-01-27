from __future__ import annotations

import re
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.modules.authn.consts import (
    REFRESH_SEPARATOR,
    MAX_REFRESH_TOKEN_LEN,
    MAX_RID_LEN,
    MAX_SECRET_LEN,
    REDIS_PREFIX_REFRESH,
    REDIS_PREFIX_TOKENVER,
)


@dataclass(frozen=True)
class RefreshTokenPair:
    rid: str
    secret: str


_RE_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_RE_SAFE_SEG = re.compile(r"^[A-Za-z0-9._~-]+$")



def _sha256(s: str) -> str:
    """
    将字符串 s 散列/哈希成固定长度，之后转为 64 位的十六进制的字符串

    :param s: 字符串
    :return: 64 位的 16 进制的字符串
    """
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def mint_refresh_token() -> RefreshTokenPair:
    """
    生成一个刷新的 Token 对

    mint: 铸造

    :return: RefreshTokenPair
    """
    return RefreshTokenPair(rid=str(uuid.uuid4()), secret=secrets.token_urlsafe(48))


def pack_refresh(pair: RefreshTokenPair) -> str:
    """
    打包 pair 中的 rid 和 secret 字段

    :param pair: RefreshTokenPair 对象
    :return: rid.secret
    """
    return f"{pair.rid}{REFRESH_SEPARATOR}{pair.secret}"


def unpack_refresh(token: str) -> RefreshTokenPair:
    """
    将刷新 token 解析成 RefreshTokenPair 对象

    :param token: 刷新的令牌
    :return: RefreshTokenPair 对象
    """
    if not isinstance(token, str):
        raise ValueError("bad_refresh_format")
    if len(token) == 0 or len(token) > int(MAX_REFRESH_TOKEN_LEN):
        raise ValueError("bad_refresh_format")
    if REFRESH_SEPARATOR not in token:
        raise ValueError("bad_refresh_format")

    rid, secret = token.split(REFRESH_SEPARATOR, 1)
    rid = rid.strip()
    secret = secret.strip()

    if not rid or not secret:
        raise ValueError("bad_refresh_format")
    if len(rid) > int(MAX_RID_LEN) or len(secret) > int(MAX_SECRET_LEN):
        raise ValueError("bad_refresh_format")

    if not _RE_UUID.match(rid):
        raise ValueError("bad_refresh_format")
    if not _RE_SAFE_SEG.match(secret):
        raise ValueError("bad_refresh_format")

    return RefreshTokenPair(rid=rid, secret=secret)


def key_refresh(rid: str) -> str:
    """
    将 rid 包装为自定义令牌刷新的键，用来在 Redis 中标识

    :param rid: 原 Redis ID
    :return: 包装后的 Redis ID, 形式为： auth:refresh:user_id
    """
    return f"{REDIS_PREFIX_REFRESH}{rid}"


def key_tokenver(user_id: int) -> str:
    """
    将 user_id 包装为自定义的 TOKENVER 键，用来在 Redis 中标识

    :param user_id: 用户 ID
    :return: 包装后的用户 ID, 形式为： auth:tokenver:user_id
    """
    return f"{REDIS_PREFIX_TOKENVER}{int(user_id)}"


def _decode_bytes(v):
    """
    将 v 按 utf-8 的格式解码为字符串，此时 v 必须是 bytes， bytearray 类型
    如果 v 不是 bytes, bytearray 类型，则原样返回

    :param v: 待解码的对象
    :return: 解码后的字符串或原对象
    """
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8")
        except Exception:
            return None
    return v


async def get_tokenver(redis, user_id: int) -> int:
    """
    从 Redis 中获取 tokenver

    :param redis: Redis 客户端
    :param user_id: 用户 ID
    :return: 解析后的 tokenver
    """
    v = await redis.get(key_tokenver(int(user_id)))
    v = _decode_bytes(v)
    if v is None:
        return 0
    try:
        return int(v)
    except Exception:
        return 0


# todo: 这个函数在哪用的
async def bump_tokenver(redis, user_id: int) -> int:
    """
    使 redis 中的 tokenver(使用 user_id 封装) 自增

    :param redis: Redis 客户端
    :param user_id: 用户 ID
    :return: 自增后的 tokenver
    """
    return int(await redis.incr(key_tokenver(int(user_id))))


async def store_refresh(
        redis,
        *,
        pair: RefreshTokenPair,
        user_id: int,
        token_ver: int,
        ttl_days: int,
) -> None:
    """
    使用 redis 将刷新令牌的值设置为对应的值
    其中，redis 中刷新令牌的键的格式为 `auth:refresh:{pair.rid}`，其对应的键的格式为 `user_id:token_ver:_sha256(pair.secret)`

    :param redis: Redis 的客户端
    :param pair: RefreshTokenPair 的对象
    :param user_id: 用户 ID
    :param token_ver: Token 的版本
    :param ttl_days: 键过期的天数
    """
    val = f"{int(user_id)}|{int(token_ver)}|{_sha256(pair.secret)}"
    await redis.set(
        key_refresh(pair.rid),
        val.encode("utf-8"),
        ex=int(timedelta(days=int(ttl_days)).total_seconds())
    )


async def revoke_refresh(redis, rid: str) -> None:
    """
    使用 redis 撤销/删除刷新令牌（它的格式为 auth:refresh:rid）

    :param redis: Redis 客户端
    :param rid: Redis 的键
    """
    await redis.delete(key_refresh(rid))


# LUA脚本，这里验证并消费refresh
_LUA_VERIFY_AND_CONSUME = """
local key = KEYS[1]
local want = ARGV[1]

local v = redis.call("GET", key)
if not v then
  return nil
end

local user_id, token_ver, secret_hash = string.match(v, "^(%d+)%|(%d+)%|(.+)$")
if not user_id then
  return nil
end

if secret_hash ~= want then
  return nil
end

redis.call("DEL", key)
return {user_id, token_ver}
"""


# todo: 此函数什么时候用
async def verify_and_consume_refresh(redis, *, pair: RefreshTokenPair) -> tuple[int, int]:
    """
    使用 redis 运行 lua 脚本，用来验证并消费一个刷新令牌

    :param redis: Redis 客户端
    :param pair: RefreshTokenPair 对象
    :return: 用户 ID 和 tokenver
    """
    want_hash = _sha256(pair.secret)

    # _LUA_VERIFY_AND_CONSUME 脚本中的
    # KEYS[1] 对应于 key_refresh(pair.rid)
    # ARGV[1] 对应于 want_hash
    res = await redis.eval(_LUA_VERIFY_AND_CONSUME, 1, key_refresh(pair.rid), want_hash)        # 使用 redis 执行 lua 脚本

    if not isinstance(res, (list, tuple)) or len(res) != 2:
        return None

    user_id = _decode_bytes(res[0])
    token_ver = _decode_bytes(res[1])

    try:
        return (int(user_id), int(token_ver))
    except Exception:
        return None