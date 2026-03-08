from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_setup import setup_logging
from app.infra.blob_storage.local_fs import LocalFsStorage
from app.infra.db.engine import create_engine
from app.infra.db.session import create_session_maker
from app.infra.qdrant_client import create_qdrant_client
from app.infra.celery.celery_app import celery_app
from app.modules.kb.ingest_service import ingest_asset


@celery_app.task(name="kb.ingest_asset")
def ingest_asset_task(asset_id: int) -> dict:
    setup_logging(level=settings.log_level)

    async def _run() -> dict:
        engine = create_engine()
        sm = create_session_maker(engine)
        storage = LocalFsStorage(root_dir=str(settings.blob_local_root))
        qdrant = create_qdrant_client()

        async with sm() as db:
            res = await ingest_asset(db=db, storage=storage, qdrant=qdrant, asset_id=int(asset_id))
            return {"ok": True, "asset_id": int(asset_id), "chunks": int(res.chunks), "points": int(res.points)}

    return asyncio.run(_run())