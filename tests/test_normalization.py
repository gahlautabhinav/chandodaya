"""
tests/test_normalization.py

Unit tests for src.normalization
"""

from __future__ import annotations

from src.normalization import (
    normalize_text,
    strip_svara_marks,
    normalize_danda,
    keep_only_svara_marks,
)


def test_strip_svara_marks():
    s = "अ॒ग्निमी॑ळे"
    stripped = strip_svara_marks(s)
    # accent marks removed, base letters preserved
    assert "॑" not in stripped
    assert "॒" not in stripped
    assert stripped.startswith("अ") and "ग्नि" in stripped


def test_keep_only_svara_marks():
    s = "अ॒ग्निमी॑ळे"
    marks = keep_only_svara_marks(s)
    assert set(marks).issubset({"॑", "॒"})


def test_normalize_danda_and_whitespace():
    s = "अग्निमीळे पुरोहितं।  यज्ञस्य॥"
    norm = normalize_danda(s)
    # Should become single '|' and '||' with normalized spaces
    assert " | " in norm
    assert " || " in norm
    assert "  " not in norm


def test_full_normalize_pipeline():
    s = "अ॒ग्निमी॑ळे पु॒रोहि॑तं।  य॒ज्ञस्य॑॥"
    out = normalize_text(s, strip_svaras=True)
    # No accent marks; dandas normalized; clean spacing
    assert "॑" not in out and "॒" not in out
    assert " | " in out and " || " in out
    assert "  " not in out
