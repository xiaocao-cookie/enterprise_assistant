from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import raise_err
from app.modules.auth.models import (
    User,
    UserRoleGrant,
    Permission,
    RolePermission
)
from app.modules.authz.scope_keys import scopes_with_global
from app.modules.audit.hook import record


async def require_perms(
        db: AsyncSession,
        *,
        user: User,
        scope_key: str,
        perm_codes: list[str],
) -> None:
    """
    通过 db 查询该 user 在权限作用域 scope_key 范围内是否拥有所有的 perm_codes 权限，若没有，触发异常

    :param db: SqlAlchemy 的异步会话对象
    :param user: User 的实体
    :param scope_key: 作用域范围的标识符
    :param perm_codes: 权限编码
    """

    if int(user.is_superadmin) == 1:
        return

    if not perm_codes:
        return

    scopes = scopes_with_global(scope_key)
    role_ids = (
        await db.execute(
            select(UserRoleGrant.role_id).where(
                UserRoleGrant.user_id == user.id,
                UserRoleGrant.scope_key.in_(scopes),
            )
        )
    ).scalars().all()

    if not role_ids:
        record(
            action="rbac.role_required",
            status="deny",
            http_status=403,
            meta={"scope_key": str(scope_key), "user_id": int(user.id)},
            error_code="rbac.role_required",
        )
        raise_err("rbac.role_required", meta={"scope_key": scope_key})

    perm_codes_rows = (
        await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.perm_id == Permission.id)
            .where(
                RolePermission.role_id.in_(role_ids),
                Permission.code.in_(perm_codes),
            )
        )
    ).scalars().all()

    have = {str(x) for x in perm_codes_rows}
    missing = [p for p in perm_codes if p not in have]
    if missing:
        record(
            action="rbac.permission_missing",
            status="deny",
            http_status=403,
            meta={"scope_key": str(scope_key), "missing": list(missing), "user_id": int(user.id)},
            error_code="rbac.permission_missing",
        )
        raise_err("rbac.permission_missing", meta={"scope_key": scope_key, "missing": missing})


async def require_any_perms(
    db: AsyncSession,
    *,
    user: User,
    scope_key: str,
    perm_codes: list[str],
) -> None:
    """
    通过 db 查询 user 在权限作用域 scope_key 中是否有任何一个 perm_codes 权限

    :param db: 数据库的连接
    :param user: User
    :param scope_key: 权限作用域
    :param perm_codes: 权限编码的列表
    """
    if int(user.is_superadmin) == 1:
        return
    if not perm_codes:
        return

    scopes = scopes_with_global(scope_key)

    role_ids = (
        await db.execute(
            select(UserRoleGrant.role_id).where(
                UserRoleGrant.user_id == user.id,
                UserRoleGrant.scope_key.in_(scopes),
            )
        )
    ).scalars().all()

    if not role_ids:
        record(action="rbac.role_required", status="deny", http_status=403, meta={"scope_key": str(scope_key), "user_id": int(user.id)}, error_code="rbac.role_required")
        raise_err("rbac.role_required", meta={"scope_key": scope_key})

    rows = (
        await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.perm_id == Permission.id)
            .where(
                RolePermission.role_id.in_(role_ids),
                Permission.code.in_(perm_codes),
            )
        )
    ).scalars().all()

    have = {str(x) for x in rows}
    if not have:
        record(action="rbac.permission_missing", status="deny", http_status=403, meta={"scope_key": str(scope_key), "required_any_of": list(perm_codes), "user_id": int(user.id)}, error_code="rbac.permission_missing")
        raise_err("rbac.permission_missing", meta={"scope_key": scope_key, "required_any_of": perm_codes})