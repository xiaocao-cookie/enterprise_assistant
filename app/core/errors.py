from dataclasses import dataclass
from typing import Any, Mapping, NoReturn

from app.core.error_codes import ERROR_MESSAGES, ERROR_STATUS

# todo: 文档补充
@dataclass
class AppError(Exception):
    """ APP 的异常类 """
    code: str
    http_status: int = 400
    message: str | None = None
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message or self.code)


def resolve_message(code: str, default: str | None = None) -> str:
    """


    :param code:
    :param default:
    :return:
    """
    c = str(code or "").strip()

    if not c:
        return str(default or "")

    msg = ERROR_MESSAGES.get(c)

    if msg is not None:
        return str(msg)

    return str(default or c)


def err(
        code: str,
        *,
        http_status: int | None = None,
        message: str | None = None,
        meta: Mapping[str, Any] | None = None,
) -> AppError:
    """


    :param code:
    :param http_status:
    :param message:
    :param meta:
    :return:
    """
    c = str(code)

    status = int(http_status) if http_status else int(ERROR_STATUS.get(c, 400))

    meta_dict: dict[str, Any] | None

    if meta is None:
        meta_dict = None
    elif isinstance(meta, dict):
        meta_dict = meta
    else:meta_dict = dict(meta)

    msg = message if message else resolve_message(c, c)

    return AppError(code=c, http_status=status, message=msg, meta=meta_dict)


def raise_err(
        code: str,
        *,
        http_status: int | None = None,
        message: str | None = None,
        meta: Mapping[str, Any] | None = None,
) -> NoReturn:
    """

    :param code:
    :param http_status:
    :param message:
    :param meta:
    :return:
    """
    raise err(code, http_status=http_status, message=message, meta=meta)