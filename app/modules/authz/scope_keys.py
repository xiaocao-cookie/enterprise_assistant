from __future__ import annotations

from dataclasses import dataclass

# from app.modules.authz.consts import SCOPE_GLOBAL

SCOPE_GLOBAL = "global"

_PREFIX_WORKSPACE = "workspace:"
_PREFIX_PROJECT = "project:"
_PREFIX_RESOURCE = "resource:"

_MAX_LEN = 128


def scope_global() -> str:
    """
    返回全局作用域
    """
    return SCOPE_GLOBAL


def scope_workspace(workspace_id: int) -> str:
    """
    根据 workspace_id 生成 WorkSpace 作用域标识符

    :param workspace_id: 工作空间的 ID
    :return: 字符串，格式为 `workspace:workspace_id`
    """
    return f"{_PREFIX_WORKSPACE}{int(workspace_id)}"


def scope_project(project_id: int) -> str:
    """
    根据 project_id 生成 Project 的作用域标识符

    :param project_id: Project 的 ID
    :return: 字符串，格式为 `project:project_id`
    """
    return f"{_PREFIX_PROJECT}{int(project_id)}"


def scope_resource(resource_type: str, ref_id: int) -> str:
    """
    根据 resource_type 和 ref_id 生成资源作用域的标识符

    :param resource_type: 资源的类型，例如 doc/audio/ticket...
    :param ref_id: 资源在数据库中的唯一标识（ID）
    :return: 字符串，格式为 `resource:resource_type:ref_id`
    """
    rt = str(resource_type or "").strip()
    if not rt:
        raise ValueError("bad_resource_type")
    if ":" in rt:
        raise ValueError("bad_resource_type")
    return f"{_PREFIX_RESOURCE}{rt}:{int(ref_id)}"


@dataclass(frozen=True)
class ParsedScope:
    """ 解析后的作用域标识符对应的数据类 """
    kind: str
    workspace_id: int | None = None
    project_id: int | None = None
    resource_type: str | None = None
    ref_id: int | None = None


def parse_scope_key(scope_key: str) -> ParsedScope:
    """
    将 scope_key 解析为 ParsedScope 类的对象，如果 scope_key 不合法，抛出异常

    :param scope_key: 权限作用域的标识符
    :return: ParsedScope 对象
    """
    sk = str(scope_key or "").strip()
    if not sk or len(sk) > _MAX_LEN:
        raise ValueError("bad_scope_key")

    if sk == SCOPE_GLOBAL:
        return ParsedScope(kind="global")

    if sk.startswith(_PREFIX_WORKSPACE):
        v = sk[len(_PREFIX_WORKSPACE) :]
        return ParsedScope(kind="workspace", workspace_id=int(v))

    if sk.startswith(_PREFIX_PROJECT):
        v = sk[len(_PREFIX_PROJECT) :]
        return ParsedScope(kind="project", project_id=int(v))

    if sk.startswith(_PREFIX_RESOURCE):
        rest = sk[len(_PREFIX_RESOURCE) :]
        if ":" not in rest:
            raise ValueError("bad_scope_key")
        rt, rid = rest.split(":", 1)
        rt = rt.strip()
        if not rt or ":" in rt:
            raise ValueError("bad_scope_key")
        return ParsedScope(kind="resource", resource_type=rt, ref_id=int(rid))

    raise ValueError("bad_scope_key")


def scopes_with_global(scope_key: str) -> list[str]:
    """
    将当前的 scope_key 添加一个 Global 权限

    :param scope_key: 权限作用域标识符
    :return: 列表
    """
    sk = str(scope_key or "").strip()
    if not sk:
        return [SCOPE_GLOBAL]
    if sk == SCOPE_GLOBAL:
        return [SCOPE_GLOBAL]
    return [sk, SCOPE_GLOBAL]


