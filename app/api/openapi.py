
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.http_consts import HDR_CACHE_CONTROL, HDR_REQUEST_ID, HDR_RESPONSE_TIME_MS
from app.api.routes_consts import NO_STORE_PATHS


_COMMON_RESPONSE_HEADERS = {
    HDR_REQUEST_ID: {
        "description": "Request correlation id",
        "schema": {"type": "string"},
    },
    HDR_RESPONSE_TIME_MS: {
        "description": "Server processing time in milliseconds",
        "schema": {"type": "string"},
    },
}

_NO_STORE_HEADER = {
    HDR_CACHE_CONTROL: {
        "description": "Sensitive response, do not store",
        "schema": {"type": "string", "example": "no-store"},
    }
}


def _merge_responses(dest: dict, src: dict) -> None:
    """
    将 src 中的内容合并到 dest 中

    :param dest: 待合并的字典
    :param src: 原字典
    """
    for k, v in src.items():
        if k not in dest:
            dest[k] = v


def _ensure_error_response_schema(schema: dict) -> None:
    """
    确保异常响应的 schema 存在

    :param schema: 异常响应的模式
    """
    comps = schema.setdefault("components", {})
    schemas = comps.setdefault("schemas", {})
    if "ErrorResponse" not in schemas:
        schemas["ErrorInfo"] = {
            "title": "ErrorInfo",
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {},
                "request_id": {"type": "string"},
                "meta": {"type": "object", "additionalProperties": True},
            },
            "required": ["code", "message", "request_id"],
        }
        schemas["ErrorResponse"] = {
            "title": "ErrorResponse",
            "type": "object",
            "properties": {"error": {"$ref": "#/components/schemas/ErrorInfo"}},
            "required": ["error"],
        }


def _err_resp(desc: str) -> dict:
    """
    根据 desc(描述) 生成 JSON 格式的异常响应

    :param desc: 描述信息
    :return: 字典
    """
    return {
        "description": desc,
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
    }


def install_openapi(app: FastAPI) -> None:
    """
    为 FastAPI app 注册一个 openapi。OpenAPI 的核心作用是用 结构化文档 来定义自己的 API接口，请求，响应等

    :param app: FastAPI 的应用程序
    """
    def custom_openapi():
        """
        自定义自己的 openapi 规范

        自定义的内容包括：
            1. 给每个接口添加常见的异常响应
            2. 给每个响应增加公共的 headers
            3. 对敏感的路径设置 Cache-Control: no-store
        """
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=getattr(app, "version", "0.1.0"),
            description=app.description,
            routes=app.routes,
        )

        _ensure_error_response_schema(schema)

        common_error_responses: dict[str, dict] = {
            "400": _err_resp("Bad Request"),
            "401": _err_resp("Unauthorized"),
            "403": _err_resp("Forbidden"),
            "404": _err_resp("Not Found"),
            "409": _err_resp("Conflict"),
            "422": _err_resp("Validation Failed"),
            "429": _err_resp("Rate Limited"),
            "500": _err_resp("Internal Error"),
        }

        paths = schema.get("paths", {})
        if isinstance(paths, dict):
            for path, path_item in paths.items():
                if not isinstance(path_item, dict):
                    continue

                for _, op in path_item.items():
                    if not isinstance(op, dict):
                        continue

                    responses = op.get("responses")
                    if not isinstance(responses, dict):
                        responses = {}
                        op["responses"] = responses

                    _merge_responses(responses, common_error_responses)

                    is_no_store_endpoint = path in NO_STORE_PATHS

                    for _, resp in responses.items():
                        if not isinstance(resp, dict):
                            continue

                        hdrs = resp.get("headers")
                        if not isinstance(hdrs, dict):
                            hdrs = {}
                            resp["headers"] = hdrs

                        for hk, hv in _COMMON_RESPONSE_HEADERS.items():
                            hdrs.setdefault(hk, hv)

                        if is_no_store_endpoint:
                            for hk, hv in _NO_STORE_HEADER.items():
                                hdrs.setdefault(hk, hv)

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
