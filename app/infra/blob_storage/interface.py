from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BlobObject:
    key: str
    size_bytes: int


class StorageBackend(Protocol):
    """
    继承 Protocol 的类通常用来静态检查类型
    即： 实现了以下四个方法的都被认定为 StorageBackend 这个类
    """
    async def put_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> BlobObject: ...
    async def get_bytes(self, *, key: str) -> bytes: ...
    async def exists(self, *, key: str) -> bool: ...
    async def delete(self, *, key: str) -> None: ...