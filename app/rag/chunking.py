"""Paragraph-aware text chunking with overlap.

Chunks are the retrieval unit: small enough for precise similarity search,
large enough to preserve context. Overlap avoids losing meaning at boundaries.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    index: int


def chunk_text(
    text: str, max_chars: int = 1200, overlap_chars: int | None = None
) -> list[Chunk]:
    """Split text into overlapping chunks, preferring paragraph boundaries.

    When overlap_chars is omitted it defaults to 150, clamped to max_chars // 5
    so small max_chars values remain valid.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap_chars is None:
        overlap_chars = min(150, max_chars // 5)
    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be smaller than max_chars")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[Chunk] = []
    buffer = ""

    def flush() -> None:
        nonlocal buffer
        if buffer.strip():
            chunks.append(Chunk(text=buffer.strip(), index=len(chunks)))
        buffer = ""

    for para in paragraphs:
        if len(para) > max_chars:
            flush()
            start = 0
            while start < len(para):
                end = start + max_chars
                chunks.append(Chunk(text=para[start:end].strip(), index=len(chunks)))
                start = end - overlap_chars
            continue
        if len(buffer) + len(para) + 2 > max_chars:
            tail = buffer[-overlap_chars:] if buffer else ""
            flush()
            buffer = (tail + "\n\n" + para).strip() if tail else para
        else:
            buffer = f"{buffer}\n\n{para}".strip() if buffer else para
    flush()
    return chunks
