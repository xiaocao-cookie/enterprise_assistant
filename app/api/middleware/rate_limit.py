from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, Request
from redis.exceptions import RedisError

from app.core.errors import raise_err
from app.infra.redis_client import get_redis
from app.api.middleware.real_ip import get_real_ip
from app.modules.audit.hook import record

RL_REDIS_KEY_PREFIX = "rl"


@dataclass(frozen=True)
class RateLimitSpec:
    """
    限流规则的配置类

    :param name: 限流的规则名
    :param limit: 在指定的时间窗口内允许的最大请求次数
    :param window_seconds: 限流窗口的长度（秒）
    """
    name: str
    limit: int
    window_seconds: int


def _key_fixed_window(
        prefix: str,
        identifier: str,
        window_seconds: int,
        now_ts: int
) -> str:
    """
    根据固定时间窗口算法生成 Redis 的限流键

    :param prefix: 限流类型的前缀，一般使用限流规则名
    :param identifier: 资源标识符（例如 IP，用户 ID等）
    :param window_seconds: 限流窗口的大小
    :param now_ts: 当前的时间戳
    :return: 用于 Redis 的键
    """
    bucket = now_ts // window_seconds                                   # 将 now_ts 划分到每个固定的桶中
    return f"{RL_REDIS_KEY_PREFIX}:{prefix}:{identifier}:{bucket}"


def _to_int(v: object) -> int | None:
    """
    将任意的 v 转换成 int

    :param v: 任意对象
    :return: 整数
    """
    if v is None:
        return None
    if isinstance(v, (bytes, bytearray)):
        try:
            v = v.decode("utf-8")
        except UnicodeDecodeError:
            return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def rate_limit_ip(spec: RateLimitSpec) -> Callable:
    """
    创建基于 IP 限流的依赖函数

    :param spec: RateLimitSpec 对象，包含限流名称，次数上限和窗口长度
    :return: Callable
    """
    async def _dep(request: Request, redis=Depends(get_redis)):
        ip = get_real_ip(request) or "unknown"
        now = int(time.time())
        k = _key_fixed_window(spec.name, ip, int(spec.window_seconds), now)

        n_raw = await redis.incr(k)                     # 若 k 不存在，则 n_raw = 1
        n = _to_int(n_raw)
        if n is None:
            raise_err("error.internal", meta={"where": "rate_limit", "reason": "bad_redis_incr"})

        if n == 1:                      # 设置第一次请求的 TTL
            ttl = int(spec.window_seconds)
            if ttl <= 0:
                raise_err("error.internal", meta={"where": "rate_limit", "reason": "bad_window_seconds"})
            try:
                await redis.expire(k, ttl)
            except RedisError:
                try:
                    await redis.delete(k)
                except RedisError:
                    raise_err("error.internal", meta={"where": "rate_limit", "reason": "redis_expire_failed"})

        if n > int(spec.limit):         # 后面的请求如果大于最大限制，则触发异常和审计
            record(
                action="http.rate_limited",
                status="deny",
                http_status=429,
                meta={"name": spec.name, "limit": int(spec.limit), "window_seconds": int(spec.window_seconds), "ip": ip},
                error_code="error.rate_limited",
            )
            raise_err(
                "error.rate_limited",
                meta={"name": spec.name, "limit": int(spec.limit), "window_seconds": int(spec.window_seconds)},
            )

    return _dep