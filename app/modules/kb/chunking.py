from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class Chunk:
    no: int
    text: str


def chunk_text(text: str) -> list[Chunk]:
    """
    文本切块，将 text 切块为 Chunk 的列表

    :param text: 文本
    :return: 列表
    """
    s = (text or "").strip()
    if not s:
        return []
    max_chars = int(settings.kb_chunk_max_chars)
    overlap = int(settings.kb_chunk_overlap_chars)
    if max_chars <= 100:
        max_chars = 100
    if overlap < 0:
        overlap = 0
    if overlap >= max_chars:
        overlap = max_chars // 5

    out: list[Chunk] = []
    i = 0
    n = 0
    L = len(s)
    while i < L:
        j = min(L, i + max_chars)
        part = s[i:j].strip()
        if part:
            out.append(Chunk(no=n, text=part))
            n += 1
        if j >= L:
            break
        i = max(0, j - overlap)
    return out