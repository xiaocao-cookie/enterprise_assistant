from __future__ import annotations

import re

from app.modules.kb.utils import sha256_bytes

_RE_SAFE = re.compile(r"[^A-Za-z0-9._-]+")

def _safe_name(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return "file"
    s = _RE_SAFE.sub("_", s)
    return s[:200] if len(s) > 200 else s


def asset_original_key(*, workspace_id: int, asset_id: int, filename: str) -> str:
    fn = _safe_name(filename)
    return f"ws/{int(workspace_id)}/assets/{int(asset_id)}/original/{fn}"


def asset_derivative_key(*, workspace_id: int, asset_id: int, name: str) -> str:
    nm = str(name or "").strip() or "derivative"
    salt = sha256_bytes(f"{int(workspace_id)}:{int(asset_id)}:{nm}".encode("utf-8"))[:16]
    return f"kb/ws/{int(workspace_id)}/assets/{int(asset_id)}/derived/{salt}/{nm}"