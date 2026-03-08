from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.infra.db.base import Base


class KBAsset(Base):
    """
        知识库表
    """
    __tablename__ = "kb_assets"
    __table_args__ = (
        Index("idx_kb_asset_ws", "workspace_id", "created_at"),
        Index("idx_kb_asset_status", "status", "created_at"),
        Index("idx_kb_asset_proj", "project_id", "created_at"),
        {"comment": "Knowledge base assets (documents/audio/video/images)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("workspaces.id"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("projects.id"), nullable=True)

    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("resources.id"), nullable=True)

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)

    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 归类，用于区分到底是音频，视频，图片，文本

    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 上传完毕后会被计算出一个校验信息

    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'pending'"))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # 这个列的类型是JSON类型，这列是额外元数据，也可以是暂时没想到的

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class KBChunk(Base):
    """
        知识库分块的表格
    """
    __tablename__ = "kb_chunks"
    __table_args__ = (
        UniqueConstraint("asset_id", "chunk_no", name="uq_kb_chunk_asset_no"),
        Index("idx_kb_chunk_asset", "asset_id"),                        # 查一个文档所有的切块
        Index("idx_kb_chunk_ws", "workspace_id", "asset_id"),
        {"comment": "Chunk registry for assets"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kb_assets.id"), nullable=False)

    workspace_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("workspaces.id"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("projects.id"), nullable=True)

    chunk_no: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    token_count: Mapped[int | None] = mapped_column(BigInteger, nullable=False)             # 加一个 token 预算

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.current_timestamp())


class KBIndexJob(Base):
    """
        知识库异步嵌入的任务表格
    """
    __tablename__ = "kb_index_jobs"
    __table_args__ = (
        UniqueConstraint("asset_id", "job_kind", name="uq_kb_job_asset_kind"),
        Index("idx_kb_job_ws", "workspace_id", "created_at"),
        Index("idx_kb_job_status", "status", "created_at"),
        {"comment": "Index jobs per asset"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("workspaces.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kb_assets.id"), nullable=False)

    job_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'queued'"))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

