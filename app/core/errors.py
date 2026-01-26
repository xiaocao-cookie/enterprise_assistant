from dataclasses import dataclass
from typing import Any, Mapping, NoReturn

from app.core.error_codes import ERROR_MESSAGES, ERROR_STATUS

# todo: 文档补充
@dataclass
class AppError(Exception):
    """ FastAPI app 的异常类, 用于包装异常 """
    code: str
    http_status: int = 400
    message: str | None = None
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """
        这段函数是在 dataclass 执行 __init__ 之后进行，主要用来补充其对父类的初始化逻辑
        """
        Exception.__init__(self, self.message or self.code)


def resolve_message(code: str, default: str | None = None) -> str:
    """
    将异常编码 code 解析为 ERROR_MESSAGE 中的异常说明，如果在 ERROR_MESSAGE 中无对应的 code，则返回 default（若存在） 或 code

    :param code: 异常编码
    :param default: 保底策略
    :return: code/message/default
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