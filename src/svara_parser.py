# src/svara_parser.py

"""
svara_parser.py

Vedic accent (svara) parsing utilities.

We detect three main categories:

- 'udatta'
- 'anudatta'
- 'svarita'
- 'none' (no explicit accent mark)

Based on Unicode Vedic signs:

Primary (Devanagari block)
--------------------------
U+0951  DEVANAGARI STRESS SIGN UDATTA       → 'udatta'
U+0952  DEVANAGARI STRESS SIGN ANUDATTA     → 'anudatta'
U+0953  DEVANAGARI GRAVE ACCENT             → 'svarita'
U+0954  DEVANAGARI ACUTE ACCENT             → 'svarita'

Vedic Extensions block: U+1CD0–U+1CE8
-------------------------------------
Treated as 'svarita' here for simplicity.
"""

from __future__ import annotations

from typing import List

from .syllabifier import Akshara


UDATTA_SIGNS = {
    "\u0951",  # ॑
}

ANUDATTA_SIGNS = {
    "\u0952",  # ॒
}

SVARITA_SIGNS = {
    "\u0953",  # grave
    "\u0954",  # acute
}

# Vedic Extensions: treat as svarita (simplified)
for code in range(0x1CD0, 0x1CE9):
    SVARITA_SIGNS.add(chr(code))


def detect_svara_for_akshara_text(text: str) -> str:
    """
    Given the raw text of an akṣara (including accent marks),
    detect its dominant svara.

    Precedence:
    -----------
    - If any anudātta sign appears → 'anudatta'
    - Else if any udātta sign     → 'udatta'
    - Else if any svarita sign    → 'svarita'
    - Else 'none'
    """
    has_anudatta = False
    has_udatta = False
    has_svarita = False

    for ch in text:
        if ch in ANUDATTA_SIGNS:
            has_anudatta = True
        elif ch in UDATTA_SIGNS:
            has_udatta = True
        elif ch in SVARITA_SIGNS:
            has_svarita = True

    if has_anudatta:
        return "anudatta"
    if has_udatta:
        return "udatta"
    if has_svarita:
        return "svarita"
    return "none"


def svara_sequence_for_aksharas(aksharas: List[Akshara]) -> List[str]:
    """
    Compute svara label for each akṣara in order.
    """
    return [detect_svara_for_akshara_text(a.text) for a in aksharas]
