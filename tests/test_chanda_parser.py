"""
tests/test_chanda_parser.py

Unit tests for src.chanda_parser
"""

from __future__ import annotations

from src.chanda_parser import parse_chanda_cell, compute_deviation_D


def test_parse_simple_gayatri():
    cell = "गायत्री"
    parsed_list = parse_chanda_cell(cell)
    assert len(parsed_list) == 1
    p = parsed_list[0]
    assert p.base_meter == "gayatri"
    assert p.deviation_label is None


def test_parse_yajur_heterometric():
    cell = "स्वराड्बृहती, ब्राह्मी उष्णिक्,"
    parsed_list = parse_chanda_cell(cell)
    # Two non-empty components
    assert len(parsed_list) == 2

    first = parsed_list[0]
    second = parsed_list[1]

    # First one should detect a base meter "brihati" and deviation "svaraj" (or variant)
    assert "brihati" in (first.base_meter or "")
    # Second likely "ushnih"
    assert "ushnih" in (second.base_meter or "")


def test_compute_deviation_D():
    from src.chanda_parser import ParsedChanda

    p = ParsedChanda(
        raw="गायत्री",
        base_meter="gayatri",
        variant_prefixes=[],
        deviation_label=None,
        deviation_D=None,
    )
    # exact 8 syllables -> D=0
    p2 = compute_deviation_D(p, actual_syllables_per_pada=8)
    assert p2.deviation_D == 0

    # 9 syllables (bhurik) -> D=1
    p3 = compute_deviation_D(p, actual_syllables_per_pada=9)
    assert p3.deviation_D == 1
