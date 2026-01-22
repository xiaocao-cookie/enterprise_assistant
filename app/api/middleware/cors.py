from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware


def install_cors(
    app,
    *,
    allow_origins: list[str],
    allow_credentials: bool,
    allow_methods: list[str],
    allow_headers: list[str],
) -> None:
    """


    :param app:
    :param allow_origins:
    :param allow_credentials:
    :param allow_methods:
    :param allow_headers:
    :return:
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )
