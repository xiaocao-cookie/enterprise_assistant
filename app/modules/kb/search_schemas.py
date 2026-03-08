from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SearchMode = Literal["bm25", "dense", "hybrid"]


class SearchReq(BaseModel):
    q: str = Field(min_length=1, max_length=4000)
    mode: SearchMode = "hybrid"
    top_k: int = Field(default=10, ge=1, le=50)
    project_id: int | None = None


class SearchHit(BaseModel):
    chunk_id: int
    asset_id: int
    score: float
    sources: list[str]
    content: str


class SearchResp(BaseModel):
    q: str
    mode: SearchMode
    top_k: int
    items: list[SearchHit]