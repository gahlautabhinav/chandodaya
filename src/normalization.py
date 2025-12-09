"""
normalization.py

Utilities for Unicode normalization and basic Devanagari cleaning for
Vedic + classical Sanskrit metrical analysis.

Main responsibilities
---------------------
- Normalize Unicode to NFC
- Normalize whitespace
- Normalize danda signs (।, ॥, |, ||, /)
- Standardize common Devanagari punctuation variants
- Strip or preserve Vedic svara marks on demand

Design notes
------------
We split concerns into small, composable functions, and expose a single
`normalize_text` orchestrator with flags.

We do *not* alter semantic letters (क, आ, ङ etc); we only:
- unify presentation variants
- optionally drop combining accent marks
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Set

# Devanagari danda characters and ASCII approximations
DANDA_CHARS = {
    "।": "|",   # single danda (pāda boundary)
    "॥": "||",  # double danda (verse boundary)
    "/": "|",
    "\\": "|",
}

# Vedic accent and related combining marks (Devanagari)
# (This list can be extended as needed.)
SVARA_MARKS: Set[str] = {
    "\u0951",  # ॑ Vedic tone Udatta
    "\u0952",  # ॒ Vedic tone Anudatta
    "\u0953",  # ॓ Grave
    "\u0954",  # ॔ Acute
    "\u1CD0",  # Vedic tone karshana etc. (rare)
    "\u1CD1",
    "\u1CD2",
    "\u1CD3",
    "\u1CD4",
    "\u1CD5",
    "\u1CD6",
    "\u1CD7",
    "\u1CD8",
    "\u1CD9",
    "\u1CDA",
    "\u1CDB",
    "\u1CDC",
    "\u1CDD",
    "\u1CDE",
    "\u1CDF",
    "\u1CE0",
    "\u1CE1",
    "\u1CE2",
    "\u1CE3",
    "\u1CE4",
    "\u1CE5",
    "\u1CE6",
    "\u1CE7",
    "\u1CE8",
    "\u1CF2",
    "\u1CF3",
    "\u1CF4",
}

_WHITESPACE_RE = re.compile(r"\s+", flags=re.UNICODE)


def to_nfc(text: str) -> str:
    """
    Normalize Unicode to NFC (Canonical Composition).

    Parameters
    ----------
    text : str
        Any Unicode string.

    Returns
    -------
    str
        NFC-normalized string.
    """
    return unicodedata.normalize("NFC", text)


def normalize_whitespace(text: str) -> str:
    """
    Collapse consecutive whitespace into single spaces, strip edges.

    This keeps line breaks only where explicitly needed; for metrical
    analysis we typically run line-by-line or on padas, so we normalize
    within a single logical line.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_danda(text: str) -> str:
    """
    Normalize danda signs and their ASCII/HTML equivalents.

    Rules
    -----
    - '।' -> '|'
    - '॥' -> '||'
    - '/' and '\\' used as separators -> '|'
    - Ensure no accidental triple-bar '|||'

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """
    out = []
    for ch in text:
        if ch in DANDA_CHARS:
            out.append(DANDA_CHARS[ch])
        else:
            out.append(ch)
    text = "".join(out)

    # Fix accidental '|||'
    text = text.replace("|||", "||")
    # Normalize spacing around danda
    text = re.sub(r"\s*\|\|\s*", " || ", text)
    text = re.sub(r"\s*\|\s*", " | ", text)
    return normalize_whitespace(text)


def strip_svara_marks(text: str) -> str:
    """
    Remove Vedic accent combining marks while preserving base letters.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """
    return "".join(ch for ch in text if ch not in SVARA_MARKS)


def keep_only_svara_marks(text: str) -> str:
    """
    Extract only the svara marks from a string (for alignment debugging).

    Parameters
    ----------
    text : str

    Returns
    -------
    str
        String containing only svara characters (order preserved).
    """
    return "".join(ch for ch in text if ch in SVARA_MARKS)


def normalize_text(
    text: str,
    *,
    strip_svaras: bool = False,
    normalize_dandas: bool = True,
    normalize_ws: bool = True,
) -> str:
    """
    High-level normalization for Sanskrit metrical analysis.

    Typical pipeline:
    - Unicode NFC
    - (optional) remove svara marks
    - normalize danda
    - normalize whitespace

    Parameters
    ----------
    text : str
    strip_svaras : bool, default False
        If True, remove all recognized Vedic accent marks.
    normalize_dandas : bool, default True
        If True, normalize danda symbols to '|' and '||'.
    normalize_ws : bool, default True
        If True, collapse whitespace as per `normalize_whitespace`.

    Returns
    -------
    str
    """
    text = to_nfc(text)
    if strip_svaras:
        text = strip_svara_marks(text)
    if normalize_dandas:
        text = normalize_danda(text)
    elif normalize_ws:
        text = normalize_whitespace(text)
    return text


if __name__ == "__main__":
    sample = "अ॒ग्निमी॑ळे पु॒रोहि॑तं। य॒ज्ञस्य॑॥"
    print("Original:", sample)
    print("NFC:", to_nfc(sample))
    print("Danda-normalized:", normalize_danda(sample))
    print("Svaras stripped:", strip_svara_marks(sample))
    print("Full normalize:", normalize_text(sample, strip_svaras=True))
