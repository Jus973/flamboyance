"""Tests for Groq JSON edit parsing (no network)."""

import pytest

from orchestrator.groq_llm import _parse_json_edits


def test_parse_plain_json():
    raw = '{"a.py": "x", "b.py": "y"}'
    out = _parse_json_edits(raw, ["a.py", "b.py"])
    assert out == {"a.py": "x", "b.py": "y"}


def test_parse_fenced_json():
    raw = 'Here:\n```json\n{"a.py": "new"}\n```'
    out = _parse_json_edits(raw, ["a.py"])
    assert out == {"a.py": "new"}


def test_rejects_extra_keys():
    with pytest.raises(ValueError, match="disallowed"):
        _parse_json_edits('{"a.py": "1", "evil.py": "2"}', ["a.py"])


def test_rejects_missing_keys():
    with pytest.raises(ValueError, match="missing"):
        _parse_json_edits('{"a.py": "1"}', ["a.py", "b.py"])
