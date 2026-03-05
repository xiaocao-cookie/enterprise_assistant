from fastapi import APIRouter, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from redis.exceptions import RedisError

from app.core.api_schemas import ApiResponse
from app.core.api_response import ok
from app.core.config import settings


router = APIRouter(tags=["system"])


@router.get("/healthz", response_model=ApiResponse[dict])
async def healthz():
    """
    测试 FastAPI app 是否正常运行
    :return: ApiResponse
    """
    return ok({"ok": True})


@router.get("/readyz", response_model=ApiResponse[dict])
async def readyz(request: Request):
    """
    检测 db，redis，es 是否正常运行

    :param request: HTTP 的请求对象
    :return: ApiResponse
    """
    db_ok = False
    redis_ok = False
    es_ok = False

    try:
        session_maker = request.app.state.db_session_maker
        async with session_maker() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except (AttributeError, SQLAlchemyError):
        pass

    try:
        redis = request.app.state.redis
        await redis.ping()
        redis_ok = True
    except (AttributeError, RedisError, TimeoutError, OSError):
        pass

    try:
        es = request.app.state.es
        es_ok = bool(await es.ping())
    except Exception:
        es_ok = False

    try:
        q = request.app.state.qdrant
        q.get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False

    ok_all = bool(db_ok and redis_ok and es_ok and qdrant_ok)
    return ok({"ok": ok_all, "deps": {"db": db_ok, "redis": redis_ok, "es": es_ok, "qdrant": qdrant_ok}})


@router.get("/version", response_model=ApiResponse[dict])
async def version():
    """
    检查 FastAPI app 的名称和环境
    """
    return ok({"app": settings.app_name, "env": settings.env})