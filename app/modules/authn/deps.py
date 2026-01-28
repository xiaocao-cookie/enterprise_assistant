from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.errors import raise_err
from app.core.config import settings
from app.core.request_context import set_user_id
from app.infra.db.deps import get_db
from app.infra.redis_client import get_redis
from app.modules.auth.models import User
from app.modules.authn.service import get_tokenver
from app.modules.security.jwt import decode_access_token
from app.modules.audit.hook import record


bearer_scheme = HTTPBearer(auto_error=False)    # 当 HTTP 请求头没有带 `Authorization` 字段，不会引发异常

async def get_current_user(
        creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
        redis = Depends(get_redis),
) -> User:
    """
    从 cred.credentials（令牌） 中解析出 user_id 与 token_ver（1），
    之后通过 redis 获取 user_id 对应的 token_ver（2）, 验证两个 token_ver 是否匹配
    若匹配，
        - 则通过 db 操纵 pgSql 来获取当前的登录用户
    若不匹配，
        - 引发异常和审计

    其他：
    HTTPAuthorizationCredentials 对象具体如下，其包含两个部分，一个是 schema，另一个是 credentials
    例如：
    ```
    Authorization: Bearer deadbeef12346
    ```
    在上述例子中:

    * `scheme` 对应 `"Bearer"`
    * `credentials` 对应 `"deadbeef12346"`

    :param creds: HTTPAuthorizationCredentials 对象，依赖 HTTPBearer
    :param db: 数据库的操作对象，依赖 get_db
    :param redis: Redis 的操作对象，依赖 get_redis
    :return: User
    """
    if creds is None or not creds.credentials:
        record(
            action="auth.bearer_required",
            status="deny",
            http_status=401,
            meta={"where": "get_current_user"},
        )
        raise_err("auth.bearer_required")

    token = creds.credentials

    try:
        payload = decode_access_token(
            token=token,
            secret=settings.jwt_secret,
            issuer=settings.jwt_issuer,
            alg=settings.jwt_alg.value,
        )
    except ValueError:
        record(
            action="auth.access_token_invalid",
            status="deny",
            http_status=401,
            meta={"where": "get_current_user"}
        )
        raise_err("auth.access_token_invalid")

    current_ver = await get_tokenver(redis, payload.user_id)
    if int(payload.token_ver) != int(current_ver):
        record(
            action="auth.access_token_expired",
            status="deny",
            http_status=401,
            meta={"where": "get_current_user", "user_id": int(payload.user_id)},
        )
        raise_err("auth.access_token_expired")

    user = (await db.execute(select(User).where(User.id == payload.user_id))).scalar_one_or_none()
    if not user or not bool(user.is_active):
        record(
            action="auth.user_inactive",
            status="deny",
            http_status=401,
            meta={"where": "get_current_user", "user_id": int(payload.user_id)},
        )
        raise_err("auth.user_inactive")

    set_user_id(int(user.id))
    return user