from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateAssetReq(BaseModel):
    filename: str = Field(min_length=1, max_length=512)
    title: str | None = Field(default=None, max_length=512)
    mime_type: str | None = Field(default=None, max_length=128)
    project_id: int | None = None
    resource_type: str = Field(min_length=1, max_length=32)
    meta: dict[str, Any] | None = None


class AssetResp(BaseModel):
    id: int
    workspace_id: int
    project_id: int | None
    created_by: int
    resource_type: str
    resource_id: int | None
    filename: str
    title: str | None
    mime_type: str | None
    source_type: str | None
    size_bytes: int | None
    sha256: str | None
    storage_key: str | None
    status: str
    error: str | None
    meta: dict[str, Any] | None
    created_at: str
    updated_at: str


class UploadResp(BaseModel):
    asset_id: int
    storage_key: str
    size_bytes: int
    sha256: str


class EnqueueIngestResp(BaseModel):
    ok: bool = True
    task_name: str = "kb.ingest_asset"
    asset_id: int