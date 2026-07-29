from app.core.security import exceeds_limit, sanitize_text


def test_sanitize_strips_control_characters() -> None:
    assert sanitize_text("a\x00b\x08c\x1bd") == "abcd"


def test_sanitize_preserves_newlines_and_tabs() -> None:
    assert sanitize_text("line one\nline two\ttabbed") == "line one\nline two\ttabbed"


def test_exceeds_limit() -> None:
    assert exceeds_limit("abc", 2)
    assert not exceeds_limit("abc", 3)
