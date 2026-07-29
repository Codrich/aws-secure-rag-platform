import pytest

from app.rag.chunking import chunk_text


def test_short_text_single_chunk() -> None:
    chunks = chunk_text("Hello world.", max_chars=100)
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world."


def test_paragraphs_grouped_within_limit() -> None:
    text = "Para one.\n\nPara two.\n\nPara three."
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) == 1


def test_long_text_splits_with_overlap() -> None:
    text = "\n\n".join(f"Paragraph {i} " + "x" * 80 for i in range(10))
    chunks = chunk_text(text, max_chars=200, overlap_chars=40)
    assert len(chunks) > 1
    assert all(len(c.text) <= 240 for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_oversized_paragraph_is_split() -> None:
    chunks = chunk_text("y" * 5000, max_chars=1000, overlap_chars=100)
    assert len(chunks) >= 5


def test_invalid_overlap_rejected() -> None:
    with pytest.raises(ValueError):
        chunk_text("text", max_chars=100, overlap_chars=100)
