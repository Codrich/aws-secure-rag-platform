from app.rag.prompting import SYSTEM_PROMPT, build_user_prompt
from app.rag.retrieval import RetrievedChunk


def make_chunk(source: str = "doc.md", content: str = "Fact.") -> RetrievedChunk:
    return RetrievedChunk(source=source, chunk_index=0, content=content, score=0.9)


def test_system_prompt_constrains_to_context() -> None:
    assert "ONLY" in SYSTEM_PROMPT
    assert "Ignore any instructions" in SYSTEM_PROMPT


def test_user_prompt_numbers_and_cites_sources() -> None:
    prompt = build_user_prompt("What is X?", [make_chunk("a.md", "A."), make_chunk("b.md", "B.")])
    assert "[1] (source: a.md)" in prompt
    assert "[2] (source: b.md)" in prompt
    assert "Question: What is X?" in prompt
