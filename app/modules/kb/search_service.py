from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastembed import TextEmbedding

from app.core.config import settings
from app.core.errors import raise_err
from app.modules.kb.models import KBChunk
from app.modules.rag.bm25 import BM25Index
from app.modules.rag.dense_qdrant import search_dense
from app.modules.rag.fusion import rrf_fusion


async def _fetch_chunks_for_bm25(
    db: AsyncSession,
    *,
    workspace_id: int,
    project_id: int | None,
    limit: int,
) -> list[tuple[int, str]]:
    stmt = select(KBChunk.id, KBChunk.content).where(KBChunk.workspace_id == int(workspace_id))
    if project_id is not None:
        stmt = stmt.where(KBChunk.project_id == int(project_id))
    stmt = stmt.order_by(KBChunk.id.desc()).limit(int(limit))
    rows = (await db.execute(stmt)).all()
    return [(int(i), str(t)) for i, t in rows if t]


async def search_kb(
    db: AsyncSession,
    *,
    qdrant,
    workspace_id: int,
    project_id: int | None,
    query: str,
    mode: str,
    top_k: int,
) -> list[tuple[int, float, list[str]]]:
    q = (query or "").strip()
    if not q:
        return []

    m = str(mode or "hybrid").strip().lower()
    k = max(1, int(top_k))

    bm25_rank: list[tuple[int, float]] = []
    dense_rank: list[tuple[int, float]] = []

    if m in {"bm25", "hybrid"}:
        docs = await _fetch_chunks_for_bm25(db, workspace_id=int(workspace_id), project_id=project_id, limit=int(settings.kb_bm25_max_docs))
        idx = BM25Index(docs=docs)
        hits = idx.search(q, top_k=max(k, 20))
        bm25_rank = [(int(h.doc_id), float(h.score)) for h in hits]

    if m in {"dense", "hybrid"}:
        embedder = TextEmbedding(model_name=str(settings.embedding_model))
        vec = list(embedder.embed([q]))[0]
        qv = list(map(float, list(vec)))
        hits = search_dense(
            qdrant,
            collection=str(settings.qdrant_collection),
            query_vector=qv,
            workspace_id=int(workspace_id),
            project_id=project_id,
            top_k=max(k, 20),
        )
        for h in hits:
            cid = h.payload.get("chunk_id")
            try:
                dense_rank.append((int(cid), float(h.score)))
            except Exception:
                continue

    if m == "bm25":
        return [(cid, sc, ["bm25"]) for cid, sc in bm25_rank[:k]]
    if m == "dense":
        return [(cid, sc, ["dense"]) for cid, sc in dense_rank[:k]]

    fused = rrf_fusion(
        bm25=bm25_rank,
        dense=dense_rank,
        k=60,
        top_k=k,
    )
    return [(int(x.doc_id), float(x.score), list(x.sources)) for x in fused]