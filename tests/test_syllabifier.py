"""
tests/test_syllabifier.py

Unit tests for src.syllabifier
"""

from __future__ import annotations

from src.normalization import normalize_text
from src.syllabifier import split_aksharas, syllabify_line, aksharas_to_LG


def test_simple_word_ram():
    # रामः -> ra-maḥ ~ two syllables, both guru
    text = "रामः"
    norm = normalize_text(text, strip_svaras=True)
    aks, LG, ganas = syllabify_line(norm)

    assert len(aks) == 2
    # Expect something like G G
    assert LG.count("G") == 2


def test_simple_word_indra():
    # इन्द्रः -> in-draḥ ~ /in/ /draḥ/
    text = "इन्द्रः"
    norm = normalize_text(text, strip_svaras=True)
    aks = split_aksharas(norm)
    LG = aksharas_to_LG(aks)

    # First syllable typically light (short vowel, open), second guru
    assert len(aks) == 2
    assert LG[1] == "G"


def test_gayatri_like_line():
    # Small artificial line with 8 syllables
    text = "अग्निमीळे पुरोहितं"
    norm = normalize_text(text, strip_svaras=True)
    aks, LG, ganas = syllabify_line(norm)

    assert len(aks) == 8
    assert len(LG) == 8
    # At least some gurus
    assert "G" in LG
    # Gaṇas of length floor(8/3) = 2
    assert len(ganas) == 2
