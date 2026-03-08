from __future__ import annotations

import io

from docx import Document
from pypdf import PdfReader


def _as_text_utf8(data: bytes) -> str:
    """
    将文件（字节流存储）按 utf-8 解码为字符串

    :param data: 文件的字节流存储数据
    :return: 解码后的字符串
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""


def extract_text(*, filename: str, mime_type: str | None, data: bytes) -> str:
    """
    按文件名 filename 的后缀 或 mime_type 类型读取 data

    :param filename: 文件名
    :param mime_type: HTTP 规定的 mime_type
    :param data: 字节流数据，代表存储的文件
    :return: 读取后的文本
    """
    fn = (filename or "").lower()
    mt = (mime_type or "").lower().strip()

    if fn.endswith(".pdf") or mt == "application/pdf":
        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for p in reader.pages:
            try:
                t = p.extract_text() or ""
            except Exception:
                t = ""
            if t:
                parts.append(t)
        return "\n\n".join(parts).strip()

    if fn.endswith(".docx") or mt in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }:
        doc = Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs if p.text]
        return "\n".join(parts).strip()

    if fn.endswith(".txt") or fn.endswith(".md") or mt.startswith("text/"):
        return _as_text_utf8(data).strip()

    return ""