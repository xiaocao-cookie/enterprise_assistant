from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import (
    UniqueConstraint,
    DateTime,
    BigInteger,
    String,
    Index,
    ForeignKey,
    text
)

from app.infra.db.base import Base


"""
此文件设计的结构为如下：
Workspace
   ├── Resource (无项目归属)
   └── Project
         └── Resource
         
         
下面详细介绍一下 Workspace / Project / Resource 数据模型

Workspace 用于实现多租户组织隔离, Project 用于实现项目分组，Resource 用作统一资源抽象层

1. Workspace
    它是系统中的定义逻辑隔离单元，用于表示一个独立的组织业务域，通常对应一个公司、团队或者独立租户

2. Project
    它作用于 workspace 内部对业务资源进行进一步拆分与分组

3. Resource
    提供可操作的所有业务资源，比如 doc/audio/image/ticket/... 
    
"""


class Workspace(Base):
    __tablename__ = "workspaces"
    __table_args__ = (UniqueConstraint("name", name="uq_workspace_name"), {"comment": "Workspace/Org container"})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="Workspace ID")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="Workspace name (unique)")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Workspace description")

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


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_ws_project_name"),
        Index("idx_project_ws", "workspace_id"),
        {"comment": "Project container under workspace"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="Project ID")
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspaces.id"), nullable=False, comment="FK -> workspaces.id"
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="Project name (unique within workspace)")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Project description")

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


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (
        Index(
            "uq_resource_ws_proj_type_ref",
            "workspace_id",
            "project_id",
            "resource_type",
            "ref_id",
            unique=True,
            postgresql_where=text("project_id IS NOT NULL"),
        ),
        Index(
            "uq_resource_ws_type_ref_no_proj",
            "workspace_id",
            "resource_type",
            "ref_id",
            unique=True,
            postgresql_where=text("project_id IS NULL"),
        ),
        Index("idx_type_ref", "resource_type", "ref_id"),
        {"comment": "Unified resource directory for authorization"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True,
                                    comment="Resource row ID (internal)")
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspaces.id"), nullable=False, comment="Owning workspace id"
    )
    project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=True, comment="Owning project id (nullable)"
    )
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False,
                                               comment="doc/audio/image/ticket/... (extensible)")
    ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="Business table PK this resource refers to")
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False,
                                            comment="Creator user_id")

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