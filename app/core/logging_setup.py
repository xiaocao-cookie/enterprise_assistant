import logging
from logging.config import dictConfig
from typing import Any
from datetime import datetime, date
import dataclasses
import json

from pydantic import BaseModel

from app.core.request_context import get_request_id, get_user_id
from app.core.readction import redact_str, redact_obj


_MAX_JSON_DEPTH = 6
_MAX_STR_LEN = 8192

# todo: 文档注释
class ContextFilter(logging.Filter):
    """ 日志上下文的过滤器 """
    def filter(self, record: logging.LogRecord) -> bool:
        """

        :param record:
        :return:
        """
        rid = getattr(record, "request_id", None)
        uid = getattr(record, "user_id", None)

        if not rid:
            rid2 = get_request_id()
            if rid2:
                setattr(record, "request_id", rid2)

        if not uid:
            uid2 = get_user_id()
            if uid2:
                setattr(record, "user_id", uid2)

        return True


def _safe_str(s: str) -> str:
    """
    确保字符串 s 是安全的，也就是说，s 必须是个字符串，且不能超过最大长度，以免日志太长

    :param s: 字符串 s
    :return: 转换后的安全字符串
    """
    if not isinstance(s, str):
        s = str(s)
    if len(s) > _MAX_STR_LEN:
        return s[:_MAX_STR_LEN] + "...(truncated)"
    return s


def _bytes_to_text(b: bytes) -> str:
    """
    将字节流对象 b 解码/转换为对应的字符串，默认使用 "utf-8" 解码

    :param b: 字节流对象
    :return: 解码/转换后的字符串
    """
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return _safe_str(repr(b))


def _to_jsonable(obj: Any, *, _depth: int = 0) -> Any:
    """
    将任意对象 obj （递归）变为可 JSON 化的对象，并且此对象的嵌套深度不能超过 _MAX_JSON_DEPTH(默认为6)

    :param obj: 任意对象
    :param _depth: 转换成可 JSON 化的对象的深度
    :return: Any

    具体描述：
    a. 如果深度 _depth > MAX_JSON_DEPTH (默认是 6)，则返回 "...(max_depth)"
    b. 否则：
        1. 如果 obj 是 bool，int，float: 直接返回 obj
        2. 如果 obj 是 str： 将其变为安全的字符串返回（调用 _safe_str() ）
        3. 如果 obj 是 bytes, bytearray, memoryview: 调用 _bytes_to_text
        4. 如果 obj 是 datetime,date: 将其变为 ISO-8601 格式的日期返回
        5. 如果 obj 是 pydantic 的 BaseModel：
            - 则将其变为字典后（obj.model_dump()）再递归 JSON 化，每次递归深度(_depth) 加 1
            - 若无法将其递归 JSON 化，则将其变为安全的字符串（调用 _safe_str()）
        6. 如果 obj 是 dataclass:
            - 则将其变为字典后（dataclass.asDict(obj)）递归 JSON 化，每次递归深度(_depth) 加 1
            - 若无法将其递归 JSON 化，则将其变为安全的字符串（调用 _safe_str() ）
        7. 如果 obj 是 字典：
            - 将字典的每一个键转换为安全的字符串（调用 _safe_str() ）
            - 将字典的每一个值递归的 JSON 化
        8. 如果 obj 是 list,tuple: 遍历 obj 中的元素并分别将其递归的 JSON 化
        9. 如果 obj 是 set: 遍历 obj 中的元素并分别将其递归的 JSON 化
        10. 如果 obj 是 BaseException: 则返回自定义的字典，形如：
            ```python
            {
            "type": obj.__class__.__name__,
            "message": _safe_str(str(obj))
            }
            ```
        11. 如果 obj 为 None: 返回 None

    c. 保底策略： 若如上条件都不满足，直接调用 _safe_str()
    """
    if _depth > _MAX_JSON_DEPTH:
        return "...(max_depth)"

    if not obj:
        return None

    if isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return _safe_str(obj)
    if isinstance(obj, (bytes, bytearray, memoryview)):
        return _bytes_to_text(bytes(obj))

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, BaseModel):
        try:
            return _to_jsonable(obj.model_dump(), _depth=_depth + 1)
        except (TypeError, ValueError):
            return _safe_str(str(obj))

    if dataclasses.is_dataclass(obj):
        try:
            return _to_jsonable(dataclasses.asdict(obj), _depth=_depth + 1)
        except (TypeError, ValueError):
            return _safe_str(str(obj))

    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            kk = _safe_str(k)
            out[kk] = _to_jsonable(v, _depth=_depth + 1)
        return out

    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x, _depth=_depth + 1) for x in obj]
    if isinstance(obj, set):
        return [_to_jsonable(x, _depth=_depth + 1) for x in obj]

    if isinstance(obj, BaseException):
        return {"type": obj.__class__.__name__, "message": _safe_str(str(obj))}

    return _safe_str(str(obj))


class JsonFormatter(logging.Formatter):
    """ JSON 格式化类 """
    def format(self, record: logging.LogRecord) -> str:
        """

        :param record:
        :return:
        """
        payload: dict[str, Any] = {
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        rid = getattr(record, "request_id", None) or get_request_id()
        uid = getattr(record, "user_id", None)
        if uid is None:
            uid = get_user_id()

        if rid:
            payload["request_id"] = rid
        if uid is not None:
            payload["user_id"] = uid

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        for k, v in record.__dict__.items():
            if k in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            if k in payload:
                continue
            payload[k] = v

        safe_payload = _to_jsonable(payload)
        safe_payload = redact_obj(safe_payload)

        try:
            return json.dumps(safe_payload, ensure_ascii=False)
        except (TypeError, ValueError, OverflowError):
            fallback = {
                "level": record.levelname.lower(),
                "logger": record.name,
                "message": _safe_str(record.getMessage()),
                "request_id": rid,
                "user_id": uid,
                "format_error": True,
            }
            return json.dumps(redact_obj(_to_jsonable(fallback)), ensure_ascii=False)


def setup_logging(*, level: str = "INFO") -> None:
    """


    :param level:
    :return:
    """
    level = (level or "INFO").upper()

    cfg = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "context": {"()": "app.core.logging_setup.ContextFilter"},
        },
        "formatters": {
            "json": {"()": "app.core.logging_setup.JsonFormatter"},
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["context"],
                "level": level,
            }
        },
        "root": {"handlers": ["stdout"], "level": level},
        "loggers": {
            "uvicorn": {"level": level},
            "uvicorn.error": {"level": level},
            "uvicorn.access": {"level": level, "propagate": False, "handlers": ["stdout"]},
            "access": {"level": level, "propagate": False, "handlers": ["stdout"]},
        },
    }

    dictConfig(cfg)
