from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PayloadSchemaType, PointStruct, VectorParams

@dataclass(frozen=True)
class DenseHit:
    point_id: str
    score: float
    payload: dict[str, Any]


def ws_filter(*, workspace_id: int, project_id: int | None = None, asset_id: int | None = None) -> Filter:
    must: list[Any] = [
        FieldCondition(key="workspace_id", match=MatchValue(value=int(workspace_id))),
    ]
    if project_id is not None:
        must.append(FieldCondition(key="project_id", match=MatchValue(value=int(project_id))))
    if asset_id is not None:
        must.append(FieldCondition(key="asset_id", match=MatchValue(value=int(asset_id))))
    return Filter(must=must)


def ensure_payload_schema(client: QdrantClient, *, collection: str) -> None:
    """
    通过 client (QdrantClient) 将 Qdrant 数据库中 collection 的 payload 字段创建索引，以加速 metadata filter

    :param client: 连接 Qdrant 的客户端
    :param collection: 向量数据库中的 Collection
    :return:
    """
    client.set_payload_schema(                      # 新版本里面是 create_payload_index 这个方法
        collection_name=str(collection),
        payload_schema={
            "workspace_id": PayloadSchemaType.INTEGER,
            "project_id": PayloadSchemaType.INTEGER,
            "asset_id": PayloadSchemaType.INTEGER,
            "chunk_id": PayloadSchemaType.INTEGER,
            "resource_type": PayloadSchemaType.KEYWORD,
        },
    )


def upsert_points(
    client: QdrantClient,
    *,
    collection: str,
    points: list[PointStruct],
) -> None:
    """
    向量数据库插入数据
    """
    if not points:
        return
    client.upsert(collection_name=str(collection), points=points)


def delete_by_asset(client: QdrantClient, *, collection: str, workspace_id: int, asset_id: int) -> None:
    flt = ws_filter(workspace_id=int(workspace_id), asset_id=int(asset_id))
    client.delete(collection_name=str(collection), points_selector=flt)


def search_dense(
    client: QdrantClient,
    *,
    collection: str,
    query_vector: list[float],
    workspace_id: int,
    project_id: int | None,
    top_k: int,
) -> list[DenseHit]:
    flt = ws_filter(workspace_id=int(workspace_id), project_id=int(project_id) if project_id is not None else None)
    res = client.search(
        collection_name=str(collection),
        query_vector=list(query_vector),
        query_filter=flt,
        with_payload=True,
        limit=max(1, int(top_k)),
    )
    out: list[DenseHit] = []
    for p in res:
        payload = dict(p.payload or {})
        out.append(DenseHit(point_id=str(p.id), score=float(p.score or 0.0), payload=payload))
    return out