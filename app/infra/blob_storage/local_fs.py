from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import aiofiles

from app.infra.blob_storage.interface import StorageBackend, BlobObject


def _safe_key(key: str) -> str:
    """


    :param key:
    :return:
    """
    k = str(key or "").strip()
    if not k or k.startswith("/") or ".." in k:
        raise ValueError("bad_storage_key")
    return k.replace("\\", "/")


def _join(root: str, key: str) -> str:
    """


    :param root:
    :param key:
    :return:
    """
    key = _safe_key(key)
    p = os.path.abspath(os.path.join(root, key))
    r = os.path.abspath(root)
    if not p.startswith(r + os.sep) and p != r:
        raise ValueError("bad_storage_key")
    return p


@dataclass
class LocalFsStorage(StorageBackend):
    root_dir: str

    def _path(self, key: str) -> str:
        k = str(key or "").lstrip("/").replace("..", "_")
        return os.path.join(self.root_dir, k)

    async def put_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> BlobObject:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return BlobObject(key=str(key), size_bytes=int(len(data)))

    async def get_bytes(self, *, key: str) -> bytes:
        path = self._path(key)
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete(self, *, key: str) -> None:
        path = self._path(key)
        try:
            os.remove(path)
        except FileNotFoundError:
            return

    async def exists(self, *, key: str) -> bool:
        path = self._path(key)
        return bool(os.path.exists(path))