import logging
import uuid
from typing import Any

from fastapi import Request
from fastapi.exception_handlers import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.http_consts import STATE_REQUEST_ID, HDR_REQUEST_ID
from app.core.api_schemas import ErrorResponse, ErrorInfo
from app.core.errors import AppError, resolve_message
from app.modules.audit.hook import record


logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str:
    """
    通过 request 请求体得到当前请求的 ID，若无请求 ID，使用 uuid 生成一个

    :param request: HTTP 的请求对象
    :return: 请求 ID
    """
    rid = getattr(request.state, STATE_REQUEST_ID, None)
    if isinstance(rid, str) and rid:
        return rid
    rid = request.headers.get(HDR_REQUEST_ID)
    if rid:
        return rid
    return uuid.uuid4().hex


def _build_error(
        *,
        code: str,
        message: Any,
        request_id: str,
        meta: dict[str, Any] | None = None,
) -> dict:
    """
    结构化异常信息, 用来在后台美化报错信息

    :param code: 异常的编码
    :param message: 异常的说明
    :param request_id: 触发此次异常的请求 ID
    :param meta: 元数据
    :return: ErrorResponse 的字典
    """
    payload = ErrorResponse(error=ErrorInfo(code=code, message=message, request_id=request_id, meta=meta))
    return payload.model_dump()


def install_exception_handlers(app) -> None:
    """
    为当前的 app （本项目使用的是FastAPI）增加异常拦截
    另外，特别需要注意的是：只要异常被触发，则一定需要 record 以用来审计！！！

    :param app: 应用程序，此项目使用 FastAPI 框架
    :return: 自定义的异常信息
    """
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        """
        处理 FastAPI app 所有 request 的 exc(AppError) 信息，并返回对应的 JSONResponse

        :param request: HTTP 的请求对象
        :param exc: 异常信息
        :return: fastapi.responses 的 JSONResponse 对象
        """
        rid = _get_request_id(request)
        st = int(exc.http_status)
        record(
            action="http.app_error",
            status="error" if st >= 500 else "deny" if st in {401, 403, 429} else "error",
            http_status=st,
            meta={"path": request.url.path, "method": request.method},
            error_code=str(exc.code)
        )
        return JSONResponse(
            status_code=st,
            content=_build_error(code=str(exc.code), message=exc.message, request_id=rid, meta=exc.meta),
            headers={HDR_REQUEST_ID: rid}
        )


    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """
        处理 FastAPI app 中所有 request 请求中触发的 exc(RequestValidationError) 异常，并返回 JSONResponse

        说明：
            当客户端请求的数据格式与后端格式不匹配时，会触发 RequestValidationError，也可标记为 422：Unprocessable Entity

        :param request: HTTP 的请求对象
        :param exc: 异常信息，RequestValidationError 对象
        :return: fastapi.responses 的 JSONResponse 对象
        """
        rid = _get_request_id(request)
        record(
            action="http.validation_failed",
            status="deny",
            http_status=422,
            meta={"path": request.url.path, "method": request.method, "errors": exc.errors()},
            error_code="error.validation_failed",
        )
        return JSONResponse(
            status_code=422,
            content=_build_error(
                code="error.validation_failed",
                message=resolve_message("error.validation_failed"),
                request_id=rid,
                meta={"errors": exc.errors()},
            ),
            headers={HDR_REQUEST_ID: rid}
        )


    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        处理 FastAPI app 中所有 request 请求中触发的 exc(StarletteHTTPException) 异常，并返回 JSONResponse

        注意：
        本函数使用的 StarletteHTTPException 是 starlette.exceptions 下的 HTTPException
        （from starlette.exceptions import HTTPException as StarletteHTTPException）

        FastAPI HTTPException 是 fastapi.exceptions 下的 HTTPException
        (from fastapi.exceptions import HTTPException)

        而 FastAPI HTTPException 是 StarletteHTTPException 的子类，所以底层异常拦截使用后者

        Starlette 是一个轻量级的 ASGI Web 框架，FastAPI 是在 Starlette 之上构建的高级 API 框架
        ASGI 规定了 Web服务器 和 Web应用 如何通信

        :param request: HTTP 的请求对象
        :param exc: 异常信息，StarletteHTTPException 对象
        :return: fastapi.responses 的 JSONResponse 对象
        """
        rid = _get_request_id(request)
        detail = exc.detail

        code = "error.http"
        msg = resolve_message(code, "http_error")
        meta: dict[str, Any] | None = None

        if isinstance(detail, dict) and "code" in detail:
            code = str(detail.get("code"))
            msg = detail.get("message", resolve_message(code, code))
            meta_val = detail.get("meta")
            if meta_val is None:
                meta = None
            elif isinstance(meta_val, dict):
                meta = meta_val
            else:
                meta = {"value": meta_val}
        elif isinstance(detail, str) and detail.strip():
            code = detail.strip()
            msg = resolve_message(code, code)
            meta = None

        record(
            action="http.http_exception",
            status="deny" if int(exc.status_code) in {401, 403, 429} else "error",
            http_status=int(exc.status_code),
            meta={"path": request.url.path, "method": request.method, "detail_meta": meta},
            error_code=str(code),
        )

        return JSONResponse(
            status_code=int(exc.status_code),
            content=_build_error(code=code, message=msg, request_id=rid, meta=meta),
            headers={HDR_REQUEST_ID: rid},
        )


    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        """
        兜底策略： 处理 FastAPI app 中所有 request 请求中触发的 exc（注意这里是 Exception 对象），并记录日志和相关信息

        :param request: HTTP 的请求对象
        :param exc: 异常信息，Exception 对象
        :return: fastapi.responses 的 JSONResponse 对象
        """
        rid = _get_request_id(request)
        logger.error(
            "unhandled_error",
            extra={"request_id": rid},
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        record(
            action="http.unhandled_error",
            status="error",
            http_status=500,
            meta={"path": request.url.path, "method": request.method, "exc_type": exc.__class__.__name__},
            error_code="error.internal"
        )
        return JSONResponse(
            status_code=500,
            content=_build_error(code="error.internal", message=resolve_message("error.internal"), request_id=rid),
            headers={HDR_REQUEST_ID: rid},
        )
