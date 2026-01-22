from __future__ import annotations

from fastapi import Request
from elasticsearch import AsyncElasticsearch

from app.core.config import settings


def create_es_client() -> AsyncElasticsearch:
    """ 创建 ES 的客户端 """
    auth = None
    if (settings.elasticsearch_username or "").strip() and (settings.elasticsearch_password or "").strip():
        auth = (settings.elasticsearch_username, settings.elasticsearch_password)
    return AsyncElasticsearch(
        hosts=[settings.elasticsearch_url],
        basic_auth=auth,
        verify_certs=bool(settings.elasticsearch_verify_certs),
    )


def get_es(request: Request) -> AsyncElasticsearch:
    """
    在 FastAPI 中，从 request 请求中获取 ES 的客户端

    :param request: HTTP 的请求
    :return: AsyncElasticsearch
    """
    return request.app.state.es