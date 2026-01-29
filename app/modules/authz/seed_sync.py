from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select

from app.modules.auth.models import Role, Permission, RolePermission
from app.modules.authz.seed import ROLES, PERMISSIONS, DEFAULT_ROLE_PERMS


async def sync_authz(db: AsyncSession) -> None:
    """
    使用 db 同步 Role, Permission, RolePermission 表

    :param db: 数据库的连接
    """
    async with db.begin():
        # 角色表插入数据
        for name, desc in ROLES:
            stmt = (
                pg_insert(Role)
                .values(name=str(name), description=str(desc))
                .on_conflict_do_update(
                    index_elements=[Role.name],
                    set_={"description": str(desc)}
                )
            )
            await db.execute(stmt)

        # 权限表插入数据
        for code, desc in PERMISSIONS:
            stmt = (
                pg_insert(Permission)
                .values(code=str(code), description=str(desc))
                .on_conflict_do_update(
                    index_elements=[Permission.code],
                    set_={"description": str(desc)},
                )
            )
            await db.execute(stmt)

        role_rows = (await db.execute(select(Role))).scalars().all()
        perm_rows = (await db.execute(select(Permission))).scalars().all()

        role_map = {str(r.name): int(r.id) for r in role_rows}
        perm_map = {str(p.code): int(p.id) for p in perm_rows}

        existing = set((await db.execute(select(RolePermission.role_id, RolePermission.perm_id))).all())

        # 给角色权限表中插入数据
        for role_name, perm_codes in DEFAULT_ROLE_PERMS.items():
            rid = role_map.get(str(role_name))
            if rid is None:
                continue
            for code in perm_codes:
                pid = perm_map.get(str(code))
                if pid is None:
                    continue
                if (rid, pid) in existing:
                    continue
                db.add(RolePermission(role_id=int(rid), perm_id=int(pid)))