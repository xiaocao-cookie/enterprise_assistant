from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

from app.core.config import settings


def create_qdrant_client() -> QdrantClient:
    """
    创建与 Qdrant 连接的客户端

    :return:
    """
    api_key = settings.qdrant_api_key.strip() if settings.qdrant_api_key else None
    if api_key:
        return QdrantClient(url=str(settings.qdrant_url), api_key=str(api_key))
    return QdrantClient(url=str(settings.qdrant_url))


def ensure_collection(client: QdrantClient, *, collection: str, vector_size: int) -> None:
    """
    确保 Qdrant 的 collection 存在，若不存在，则创建大小为 vector_size 的 collection

    :param client: 连接 Qdrant 的客户端
    :param collection: Qdrant 中的某个向量集合
    :param vector_size: 默认一个 collection 存储多少个向量
    :return:
    """
    cols = client.get_collections()
    names = {c.name for c in cols.collections} if cols and cols.collections else set()
    if collection in names:
        return
    client.create_collection(
        collection_name=str(collection),
        vectors_config=VectorParams(size=int(vector_size), distance=Distance.COSINE),
    )


async def qdrant_ping(client: QdrantClient) -> bool:
    try:
        await client.get_collections()
        return True
    except Exception:
        return False