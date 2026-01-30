from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.api_schemas import ApiResponse, ActionResult
from app.core.errors import raise_err
from app.infra.db.deps import get_db
from app.infra.redis_client import get_redis
from app.api.response import ok_no_store
from app.api.middleware.rate_limit import rate_limit_ip, RateLimitSpec
from app.modules.auth.models import User
from app.modules.authn.consts import RL_AUTH_LOGIN, RL_AUTH_REFRESH, RL_AUTH_REGISTER
from app.modules.authn.schemas import (
    MeResp,
    RegisterReq,
    TokenResp,
    LoginReq,
    RefreshReq
)
from app.modules.authn.deps import get_current_user
from app.modules.authn.service import (
    bump_tokenver,
    mint_refresh_token,
    store_refresh,
    pack_refresh,
    unpack_refresh,
    revoke_refresh,
    verify_and_consume_refresh,
    get_tokenver,
)
from app.modules.security.password import hash_password, verify_password
from app.modules.security.jwt import create_access_token
from app.modules.audit.hook import record



router = APIRouter(prefix="/auth", tags=["authn 认证"])


async def _noop_dep() -> None:
    """
    无操作的依赖函数，此处用来防止接口限流关闭时，FastAPI 引发异常
    """
    return None


def _auth_rl(name: str):
    """
    生成与 name 对应的 auth 限流依赖

    :param name: 字符串
    :return: Callable 或 None
    """
    if not settings.rate_limit_enabled:
        return _noop_dep
    return rate_limit_ip(
        RateLimitSpec(
            name=name,
            limit=settings.auth_rate_limit_per_window,
            window_seconds=settings.auth_rate_limit_window_seconds,
        )
    )


_rl_register = _auth_rl(RL_AUTH_REGISTER)
_rl_login = _auth_rl(RL_AUTH_LOGIN)
_rl_refresh = _auth_rl(RL_AUTH_REFRESH)


# todo: 函数文档注释细化

@router.post(
    "/register",
    response_model=ApiResponse[MeResp],
    status_code=201,
    dependencies=[Depends(_rl_register)]
)
async def register(
        req: RegisterReq,
        response: Response,
        db: AsyncSession = Depends(get_db)
):
    """
    用户注册

    :param req: RegisterReq 的对象
    :param response: 响应
    :param db: 数据库的异步 session 客户端，依赖 get_db
    :return: ApiResponse 对象，其中 data 的类型为 MeResp
    """
    async with db.begin():                  # 开启一个数据库的 transaction(事务)
        exists = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
        if exists:
            record(
                action="auth.register",
                status="deny",
                http_status=409,
                meta={"reason": "email_taken", "email": str(req.email)},
            )
            raise_err("auth.email_taken")

        user = User(email=req.email, password_hash=hash_password(req.password))
        db.add(user)                                # 将 user 加入 session
        await db.flush()                            # 将 session 中暂存的对象写入数据库
        await db.refresh(user)                      # 自动刷新 user 并同步到数据库，适配多个用户几乎同时注册的场景

    record(
        action="auth.register",
        status="ok",
        actor_user_id=int(user.id),
        meta={"user_id": int(user.id), "email": str(user.email)},
    )

    data = MeResp(
        id=int(user.id),
        email=user.email,
        is_active=bool(user.is_active),
        is_superadmin=bool(user.is_superadmin),
    )
    return ok_no_store(response, data)


@router.post(
    "/login",
    response_model=ApiResponse[TokenResp],
    dependencies=[Depends(_rl_login)],
)
async def login(
        req: LoginReq,
        response: Response,
        db: AsyncSession = Depends(get_db),
        redis = Depends(get_redis),
):
    """
    用户登录

    :param req: LoginReq 的对象
    :param response: 响应
    :param db: 数据库的异步 session 客户端, 依赖 get_db
    :param redis: Redis 客户端
    :return: ApiResponse 对象，其中 data 的类型为 TokenResp
    """
    user = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if not user or not bool(user.is_active):
        record(
            action="auth.login",
            status="deny",
            http_status=401,
            meta={"email": str(req.email)}
        )
        raise_err("auth.credentials_invalid")
    if not verify_password(req.password, user.password_hash):
        record(
            action="auth.login",
            status="deny",
            http_status=401,
            meta={"email": str(req.email)}
        )
        raise_err("auth.credentials_invalid")

    token_ver = await bump_tokenver(redis, int(user.id))
    token_ver = int(token_ver)

    access = create_access_token(               # 生成访问者令牌
        secret=settings.jwt_secret,
        issuer=settings.jwt_issuer,
        alg=settings.jwt_alg.value,
        user_id=int(user.id),
        token_ver=int(token_ver),
        minutes=settings.access_token_expire_minutes,
    )

    pair = mint_refresh_token()         # 生成一个 RefreshTokenPair
    await store_refresh(                # 将 RefreshTokenPair 解析后存储到 Redis 中
        redis,
        pair=pair,
        user_id=int(user.id),
        token_ver=token_ver,
        ttl_days=settings.refresh_token_expire_days,
    )

    record(                             # 用户登录触发审计！！！
        action="auth.login",
        status="ok",
        actor_user_id=int(user.id),
        meta={"user_id": int(user.id)}
    )
    data = TokenResp(
        access_token=access,
        expires_in_minutes=settings.access_token_expire_minutes,
        refresh_token=pack_refresh(pair),
    )
    return ok_no_store(response, data)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResp],
    dependencies=[Depends(_rl_refresh)],
)
async def refresh(
        req: RefreshReq,
        response: Response,
        db: AsyncSession = Depends(get_db),
        redis = Depends(get_redis),
):
    """
    刷新令牌

    :param req: RefreshReq 的对象
    :param response: 响应
    :param db: 数据库的异步 session 客户端, 依赖 get_db
    :param redis: Redis 客户端
    :return: ApiResponse 对象，其中 data 的类型为 TokenResp
    """
    try:
        pair = unpack_refresh(req.refresh_token)
    except Exception:
        record(
            action="auth.refresh",
            status="deny",
            http_status=401,
            meta={"reason": "bad_format"}
        )
        raise_err("auth.refresh_token_invalid")

    consumed = await verify_and_consume_refresh(redis, pair=pair)
    if not consumed:
        record(action="auth.refresh", status="deny", http_status=401, meta={"reason": "not_found_or_mismatch"})
        raise_err("auth.refresh_token_invalid")

    user_id, token_ver = consumed
    current_ver = await get_tokenver(redis, int(user_id))
    if int(token_ver) != int(current_ver):
        record(
            action="auth.refresh",
            status="deny",
            http_status=401,
            meta={"reason": "tokenver_mismatch", "user_id": int(user_id)},
        )
        raise_err("auth.refresh_token_expired")

    user = (await db.execute(select(User).where(User.id == int(user_id)))).scalar_one_or_none()
    if not user or not bool(user.is_active):
        record(
            action="auth.refresh",
            status="deny",
            http_status=401,
            meta={"reason": "user_inactive", "user_id": int(user_id)},
        )
        raise_err("auth.user_inactive")
    access = create_access_token(  # 生成新的access token
        secret=settings.jwt_secret,
        issuer=settings.jwt_issuer,
        alg=settings.jwt_alg.value,
        user_id=int(user_id),
        token_ver=int(token_ver),
        minutes=settings.access_token_expire_minutes,
    )

    new_pair = mint_refresh_token()
    await store_refresh(
        redis,
        pair=new_pair,
        user_id=int(user_id),
        token_ver=int(token_ver),
        ttl_days=settings.refresh_token_expire_days,
    )

    record(action="auth.refresh", status="ok", actor_user_id=int(user_id), meta={"user_id": int(user_id)})

    data = TokenResp(
        access_token=access,
        expires_in_minutes=settings.access_token_expire_minutes,
        refresh_token=pack_refresh(new_pair),
    )
    return ok_no_store(response, data)


@router.post("/logout", response_model=ApiResponse[ActionResult])
async def logout(
        req: RefreshReq,
        response: Response,
        redis = Depends(get_redis),
        me: User = Depends(get_current_user)
):
    """
    用户登出

    :param req: RefreshReq 的对象
    :param response: 响应
    :param redis: Redis 客户端
    :param me: 当前用户信息，依赖 get_current_user
    :return: ApiResponse 对象，其中 data 为 ActionResult 对象，即 ok
    """
    try:
        pair = unpack_refresh(req.refresh_token)
        await revoke_refresh(redis, pair.rid)
    except Exception:
        pass                        # todo: 这里考虑刷新令牌的回收问题

    await bump_tokenver(redis, int(me.id))
    record(
        action="auth.logout",
        status="ok",
        meta={"user_id": int(me.id)}
    )
    return ok_no_store(response, ActionResult(ok=True))



@router.get("/me", response_model=ApiResponse[MeResp])
async def me(response: Response, user: User = Depends(get_current_user)):
    """
    返回个人主页

    :param response: 响应
    :param user: 当前用户
    :return: ApiResponse 对象，其中 data 为 MeResp 对象
    """
    record(action="auth.me", status="ok", meta={"user_id": int(user.id)})
    data = MeResp(
        id=int(user.id),
        email=user.email,
        is_active=bool(user.is_active),
        is_superadmin=bool(user.is_superadmin),
    )
    return ok_no_store(response, data)