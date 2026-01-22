from __future__ import annotations

from fastapi import Request


def get_real_ip(request: Request) -> str | None:
    """
    通过 HTTP 的 request 对象获得真实的 IP 地址

    :param request: HTTP 的 Request 对象
    :return: IP 地址
    """
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[0]

    xri = request.headers.get("X-Real-IP")
    if xri and xri.strip():
        return xri.strip()

    if request.client:
        return request.client.host

    return None