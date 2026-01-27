from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    text,
    DateTime,
    Index,
    UniqueConstraint,
    ForeignKey
)

from app.infra.db.base import Base


class User(Base):
    """ 用户表 """
    __tablename__ = "users"
    __table_args__ = {"comment": "System users"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="User ID (internal PK)")
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="Login email (unique)")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="Password hash (argon2id)")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), comment="Active user")
    is_superadmin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), comment="Bypass all authz"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp(), comment="Created time"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Updated time",
    )


class UserIdentity(Base):
    """
    用户身份映射表，用于将不同认证来源的用户统一映射到系统用户
    这些不同的认证来源可以是 local/google... 这样的网站，也可以是 OAuth/OIDC 这样的授权框架

    典型流程如下：
        1. 登录时通过 （provider, subject）查找对应的 user
        2. 若不存在则自动创建用户并绑定身份
        3. 支持一个用户绑定多个身份来源

    """
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_provider_subject"),
        Index("idx_user_provider", "user_id", "provider"),
        {"comment": "External identities (future SSO/OIDC/SAML)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="Identity row ID")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, comment="FK -> users.id")
    provider: Mapped[str] = mapped_column(String(32), nullable=False,
                                          comment="Provider: local/google/okta/... (future)")
    subject: Mapped[str] = mapped_column(String(255), nullable=False,
                                         comment="Provider subject (OIDC sub / SAML NameID)")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Provider email (optional)")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp(), comment="Created time"
    )


class Role(Base):
    """ 角色表 """
    __tablename__ = "roles"
    __table_args__ = {"comment": "RBAC roles"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="Role ID")
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="Role name (unique)")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Role description")


class Permission(Base):
    """ 权限表 """
    __tablename__ = "permissions"
    __table_args__ = {"comment": "Permission registry (code is stable identifier)"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="Permission ID")
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="Permission code like doc.read")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Permission description")


class RolePermission(Base):
    """ 角色权限表 """
    __tablename__ = "role_permissions"
    __table_args__ = {"comment": "Role -> Permission mapping"}

    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id"), primary_key=True, comment="FK -> roles.id")
    perm_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("permissions.id"), primary_key=True, comment="FK -> permissions.id"
    )


class UserRoleGrant(Base):
    """ 用户角色表 """
    __tablename__ = "user_role_grants"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "scope_key", name="uq_user_role_scope"),
        Index("idx_user_scope", "user_id", "scope_key"),
        Index("idx_scope", "scope_key"),
        {"comment": "User role grants scoped by scope_key"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="Grant row ID")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, comment="FK -> users.id")
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id"), nullable=False, comment="FK -> roles.id")
    scope_key: Mapped[str] = mapped_column(                         # 用户角色的作用范围
        String(128),
        nullable=False,
        comment="global | workspace:{id} | project:{id} | resource:{type}:{ref_id}",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, comment="Granting admin user_id"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp(), comment="Grant time"
    )