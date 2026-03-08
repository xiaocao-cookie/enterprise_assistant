from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

_RE_WORD = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)


def _tokenize(s: str) -> list[str]:
    if not s:
        return []
    return [m.group(0).lower() for m in _RE_WORD.finditer(s)]


@dataclass(frozen=True)
class BM25Hit:
    doc_id: int
    score: float


class BM25Index:
    def __init__(self, *, docs: list[tuple[int, str]]):
        self._ids = [int(i) for i, _ in docs]
        corpus = [_tokenize(t) for _, t in docs]
        self._bm25 = BM25Okapi(corpus)

    def search(self, query: str, *, top_k: int) -> list[BM25Hit]:
        q = _tokenize(query)
        if not q:
            return []
        scores = self._bm25.get_scores(q)
        pairs = list(zip(self._ids, scores))
        pairs.sort(key=lambda x: float(x[1]), reverse=True)
        out: list[BM25Hit] = []
        for i, s in pairs[: max(0, int(top_k))]:
            out.append(BM25Hit(doc_id=int(i), score=float(s)))
        return out