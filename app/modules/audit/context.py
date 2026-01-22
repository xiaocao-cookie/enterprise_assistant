from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_audit_events: ContextVar[list[dict[str, Any]] | None] = ContextVar("audit_events", default=None)


def init_audit_context() -> None:
    _audit_events.set([])


def clear_audit_context() -> None:
    _audit_events.set(None)


def add_audit_event(evt: dict[str, Any]) -> None:
    buf = _audit_events.get()
    if buf is None:
        return
    buf.append(evt)


def pop_audit_events() -> list[dict[str, Any]]:
    buf = _audit_events.get()

    if not buf:
        return []

    out = list(buf)
    buf.clear()

    return out