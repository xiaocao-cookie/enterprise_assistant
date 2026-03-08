from __future__ import annotations

import hashlib
from dataclasses import dataclass

from fastembed import TextEmbedding
from qdrant_client.http.models import PointStruct

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import raise_err
from app.infra.blob_storage.interface import StorageBackend
from app.modules.audit.hook import record
from app.modules.kb.chunking import chunk_text
from app.modules.kb.consts import (
    ASSET_STATUS_FAILED,
    ASSET_STATUS_INDEXING,
    ASSET_STATUS_READY,
    JOB_KIND_INGEST,
    JOB_STATUS_DONE,
    JOB_STATUS_FAILED,
    JOB_STATUS_RUNNING,
)
from app.modules.kb.extractors import extract_text
from app.modules.kb.models import KBAsset, KBChunk, KBIndexJob
from app.modules.rag.dense_qdrant import delete_by_asset, upsert_points


def _point_id(*, asset_id: int, chunk_id: int) -> str:
    return f"{int(asset_id)}:{int(chunk_id)}"


@dataclass(frozen=True)
class IngestResult:
    chunks: int
    points: int


async def ensure_job_row(db: AsyncSession, *, workspace_id: int, asset_id: int) -> KBIndexJob:
    job = (await db.execute(select(KBIndexJob).where(KBIndexJob.asset_id == int(asset_id), KBIndexJob.job_kind == JOB_KIND_INGEST))).scalar_one_or_none()
    if job:
        return job
    async with db.begin():
        job2 = KBIndexJob(workspace_id=int(workspace_id), asset_id=int(asset_id), job_kind=JOB_KIND_INGEST, status="queued", error=None)
        db.add(job2)
        await db.flush()
        await db.refresh(job2)
        return job2


async def ingest_asset(
    *,
    db: AsyncSession,
    storage: StorageBackend,
    qdrant,
    asset_id: int,
) -> IngestResult:
    a = (await db.execute(select(KBAsset).where(KBAsset.id == int(asset_id)))).scalar_one_or_none()
    if not a:
        raise_err("kb.asset_not_found")

    if not a.storage_key:
        raise_err("kb.asset_not_uploaded")

    await ensure_job_row(db, workspace_id=int(a.workspace_id), asset_id=int(a.id))

    async with db.begin():
        a.status = ASSET_STATUS_INDEXING
        a.error = None
        await db.flush()

    async with db.begin():
        j = (await db.execute(select(KBIndexJob).where(KBIndexJob.asset_id == int(a.id), KBIndexJob.job_kind == JOB_KIND_INGEST))).scalar_one_or_none()
        if j:
            j.status = JOB_STATUS_RUNNING
            j.error = None
            await db.flush()

    data = await storage.get_bytes(key=str(a.storage_key))
    text = extract_text(filename=str(a.filename), mime_type=str(a.mime_type) if a.mime_type else None, data=data)
    if not text:
        async with db.begin():
            a.status = ASSET_STATUS_FAILED
            a.error = "empty_or_unsupported"
            await db.flush()
            j2 = (await db.execute(select(KBIndexJob).where(KBIndexJob.asset_id == int(a.id), KBIndexJob.job_kind == JOB_KIND_INGEST))).scalar_one_or_none()
            if j2:
                j2.status = JOB_STATUS_FAILED
                j2.error = "empty_or_unsupported"
                await db.flush()
        raise_err("kb.ingest_unsupported", meta={"asset_id": int(a.id)})

    chunks = chunk_text(text)
    if not chunks:
        async with db.begin():
            a.status = ASSET_STATUS_FAILED
            a.error = "no_chunks"
            await db.flush()
            j2 = (await db.execute(select(KBIndexJob).where(KBIndexJob.asset_id == int(a.id), KBIndexJob.job_kind == JOB_KIND_INGEST))).scalar_one_or_none()
            if j2:
                j2.status = JOB_STATUS_FAILED
                j2.error = "no_chunks"
                await db.flush()
        raise_err("kb.ingest_failed", meta={"asset_id": int(a.id), "reason": "no_chunks"})

    embedder = TextEmbedding(model_name=str(settings.embedding_model))
    vectors = list(embedder.embed([c.text for c in chunks]))
    vecs = [list(map(float, v)) for v in vectors]
    if len(vecs) != len(chunks):
        raise_err("kb.ingest_failed", meta={"asset_id": int(a.id), "reason": "embed_mismatch"})

    async with db.begin():
        await db.execute(delete(KBChunk).where(KBChunk.asset_id == int(a.id)))
        await db.flush()

        db_chunks: list[KBChunk] = []
        for c in chunks:
            db_chunks.append(
                KBChunk(
                    workspace_id=int(a.workspace_id),
                    project_id=int(a.project_id) if a.project_id is not None else None,
                    asset_id=int(a.id),
                    chunk_no=int(c.no),
                    content=str(c.text),
                    meta=None,
                )
            )
        db.add_all(db_chunks)
        await db.flush()
        for cc in db_chunks:
            await db.refresh(cc)

    try:
        delete_by_asset(qdrant, collection=str(settings.qdrant_collection), workspace_id=int(a.workspace_id), asset_id=int(a.id))
    except Exception:
        pass

    points: list[PointStruct] = []
    for cc, v in zip(db_chunks, vecs):
        payload = {
            "workspace_id": int(a.workspace_id),
            "project_id": int(a.project_id) if a.project_id is not None else 0,
            "asset_id": int(a.id),
            "chunk_id": int(cc.id),
            "resource_type": str(a.resource_type),
        }
        points.append(PointStruct(id=_point_id(asset_id=int(a.id), chunk_id=int(cc.id)), vector=v, payload=payload))

    upsert_points(qdrant, collection=str(settings.qdrant_collection), points=points)

    async with db.begin():
        a.status = ASSET_STATUS_READY
        a.error = None
        await db.flush()
        j2 = (await db.execute(select(KBIndexJob).where(KBIndexJob.asset_id == int(a.id), KBIndexJob.job_kind == JOB_KIND_INGEST))).scalar_one_or_none()
        if j2:
            j2.status = JOB_STATUS_DONE
            j2.error = None
            await db.flush()

    record(action="kb.ingest_done", status="ok", meta={"asset_id": int(a.id), "chunks": int(len(db_chunks)), "points": int(len(points))})
    return IngestResult(chunks=int(len(db_chunks)), points=int(len(points)))