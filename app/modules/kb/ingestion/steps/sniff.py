from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SniffResult:
    mime_type: str | None
    source_type: str | None
    meta: dict[str, Any] | None


def _source_type_from_mime(m: str | None) -> str | None:
    if not m:
        return None
    ml = m.lower()
    if ml.startswith("audio/"):
        return "audio"
    if ml.startswith("video/"):
        return "video"
    if ml.startswith("image/"):
        return "image"
    if ml in {"application/pdf"}:
        return "document"
    if ml in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown",
        "text/html",
    }:
        return "document"
    return None


async def sniff(*, filename: str, mime_type_hint: str | None = None) -> SniffResult:
    mt = (mime_type_hint or "").strip() or None
    if mt is None:
        mt, _ = mimetypes.guess_type(str(filename or "").strip())
    st = _source_type_from_mime(mt)
    meta: dict[str, Any] = {"filename": str(filename or "").strip()}
    if mt:
        meta["mime_type"] = mt
    if st:
        meta["source_type"] = st
    return SniffResult(mime_type=mt, source_type=st, meta=meta or None)
