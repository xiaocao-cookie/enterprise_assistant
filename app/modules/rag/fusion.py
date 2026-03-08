from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class FusionHit:
    doc_id: int
    score: float
    sources: list[str]


def rrf_fusion(
    *,
    bm25: list[tuple[int, float]],
    dense: list[tuple[int, float]],
    k: int = 60,
    top_k: int = 20,
) -> list[FusionHit]:
    rrf: dict[int, float] = {}
    srcs: dict[int, list[str]] = {}

    def add(rank_list: list[tuple[int, float]], src: str) -> None:
        for r, (doc_id, _score) in enumerate(rank_list, start=1):
            s = 1.0 / (float(k) + float(r))
            rrf[doc_id] = float(rrf.get(doc_id, 0.0)) + s
            srcs.setdefault(doc_id, [])
            if src not in srcs[doc_id]:
                srcs[doc_id].append(src)

    add(bm25, "bm25")
    add(dense, "dense")

    items = list(rrf.items())
    items.sort(key=lambda x: float(x[1]), reverse=True)
    out: list[FusionHit] = []
    for doc_id, sc in items[: max(1, int(top_k))]:
        out.append(FusionHit(doc_id=int(doc_id), score=float(sc), sources=list(srcs.get(int(doc_id), []))))
    return out