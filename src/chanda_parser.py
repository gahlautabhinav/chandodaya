"""
chanda_parser.py

Parser/normalizer for complex chanda labels from CSVs.

Responsibilities
----------------
- Parse raw chanda cell (possibly comma-separated heterometric labels)
- Normalize names (strip whitespace, standardize transliteration, etc.)
- Separate:
    * base meter family (gayatri, trishtubh, jagati, anushtubh, etc.)
    * variant prefixes (brahmi, archi, arshi, yajushi, etc.)
    * deviation labels (nichrid, bhurik, viraj, svaraj)

Major meters (Pingala's 7)
--------------------------
We explicitly support the 7 "major" Vedic chandas families:

- gayatri  (8 syllables per pāda)
- ushnih   (7)
- anushtubh (8)
- brihati  (9)
- pankti   (8)
- trishtubh (11)
- jagati   (12)

Deviation convention
--------------------
Let:

    D = actual_syllables_per_pada - target_for_family

We use:
    -1  -> Nichrid
    +1  -> Bhurik
    +2  -> Viraj
    >=3 -> Svaraj

If the label already explicitly says svaraj/bhurik/etc., we keep that.
If it doesn't, but D matches, we infer the deviation label.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict


# --- Base meter family and their target syllables per pāda ---
BASE_METER_SYLLABLES: Dict[str, int] = {
    "gayatri": 8,
    "ushnih": 7,
    "anushtubh": 8,
    "brihati": 9,
    "pankti": 8,
    "trishtubh": 11,
    "jagati": 12,
}

# Known deviation labels in ASCII (normalized forms)
DEVIATION_LABELS = {"nichrid", "bhurik", "viraj", "svaraj"}

# Direct Devanagari → base meter mapping for common variants
DEVANAGARI_BASE_METER_MAP: Dict[str, str] = {
    # Gāyatrī
    "गायत्री": "gayatri",
    "गायत्रीः": "gayatri",
    "गायत्री छन्दः": "gayatri",
    "गायत्री छन्दस्": "gayatri",

    # Uṣṇih / Uṣṇik
    "उष्णिक्": "ushnih",
    "उष्णिह्": "ushnih",
    "उष्णिक् छन्दः": "ushnih",
    "उष्णिह् छन्दः": "ushnih",
    "उष्णिह् छन्दस्": "ushnih",

    # Anuṣṭubh / Anuṣṭup
    "अनुष्टुप्": "anushtubh",
    "अनुष्टुप् छन्दः": "anushtubh",
    "अनुष्टुभ्": "anushtubh",
    "अनुष्टुभ् छन्दः": "anushtubh",
    "अनुष्टुप् छन्दस्": "anushtubh",

    # Bṛhatī
    "बृहती": "brihati",
    "बृहतीः": "brihati",
    "बृहती छन्दः": "brihati",
    "बृहती छन्दस्": "brihati",

    # Paṅkti / Pankti
    "पङ्क्तिः": "pankti",
    "पङ्क्ति": "pankti",
    "पंक्ति": "pankti",
    "पंक्तिः": "pankti",
    "पङ्क्ति छन्दः": "pankti",

    # Triṣṭubh / Triṣṭup
    "त्रिष्टुप्": "trishtubh",
    "त्रिष्टुप् छन्दः": "trishtubh",
    "त्रिष्टुभ्": "trishtubh",
    "त्रिष्टुभ् छन्दः": "trishtubh",
    "त्रिष्टुप् छन्दस्": "trishtubh",

    # Jagatī
    "जगती": "jagati",
    "जगतीः": "jagati",
    "जगती छन्दः": "jagati",
    "जगती छन्दस्": "jagati",
}

# Some Devanagari tokens mainly indicating deviations; we normalize them.
DEVANAGARI_DEVIATION_TOKENS: Dict[str, str] = {
    "स्वराड्": "svaraj",
    "स्वराड": "svaraj",
    "स्वराड्‌": "svaraj",
    "भुरिक्": "bhurik",
    "भूरिक्": "bhurik",
    "भूरिक् छन्दः": "bhurik",
    "विराट्": "viraj",
    "विराज्": "viraj",
    "विराज": "viraj",
    "निचृत्": "nichrid",
    "निचृद्": "nichrid",
}


@dataclass
class ParsedChanda:
    raw: str
    base_meter: Optional[str]
    variant_prefixes: List[str]
    deviation_label: Optional[str]
    deviation_D: Optional[int]


def _normalize_ascii_token(tok: str) -> str:
    """
    Normalize an ASCII/romanized token into a lowercase identifier.

    This is used for both base meter names and deviation labels when
    the token is not directly present in the Devanagari lookup tables.
    """
    l_ascii = (
        tok.replace("ā", "a")
        .replace("ī", "i")
        .replace("ū", "u")
        .replace("ṛ", "r")
        .replace("ṝ", "r")
        .replace("ṅ", "n")
        .replace("ñ", "n")
        .replace("ś", "sh")
        .replace("ṣ", "sh")
        .replace("ṭ", "t")
        .replace("ḍ", "d")
        .replace("’", "")
        .replace("'", "")
    )
    return l_ascii.lower()


def normalize_label(label: str) -> str:
    """
    Normalize a single chanda label token.

    Order:
    ------
    1. Try direct Devanagari base meter mapping.
    2. Try Devanagari deviation tokens.
    3. Fallback to ASCII-ish normalization.
    """
    l = label.strip()
    if not l:
        return ""

    # 1) Exact Devanagari base meter form
    if l in DEVANAGARI_BASE_METER_MAP:
        return DEVANAGARI_BASE_METER_MAP[l]

    # 2) Explicit Devanagari deviation form?
    if l in DEVANAGARI_DEVIATION_TOKENS:
        return DEVANAGARI_DEVIATION_TOKENS[l]

    # 3) ASCII-ish fallback
    return _normalize_ascii_token(l)


def parse_chanda_cell(raw_cell: str) -> List[ParsedChanda]:
    """
    Parse a raw CSV chanda cell into ParsedChanda objects.

    - If multiple meters are separated by comma, one ParsedChanda per
      comma-separated component (pāda-wise meters).
    - Each component is split on whitespace; tokens are classified as:
        * base meter (if in BASE_METER_SYLLABLES)
        * deviation label (if in DEVIATION_LABELS)
        * otherwise variants / qualifiers (brahmi, yajushi, archi, etc.)

    Example
    -------
    "स्वराड् ब्राह्मी त्रिष्टुप्, याजुषी जगती"
        -> [
              ParsedChanda(
                  raw="स्वराड् ब्राह्मी त्रिष्टुप्",
                  base_meter="trishtubh",
                  variant_prefixes=["brahmi"],
                  deviation_label="svaraj",
                  deviation_D=None,
              ),
              ParsedChanda(
                  raw="याजुषी जगती",
                  base_meter="jagati",
                  variant_prefixes=["yajushi"],
                  deviation_label=None,
                  deviation_D=None,
              ),
           ]
    """
    if not raw_cell:
        return []

    components = [c.strip() for c in str(raw_cell).split(",") if c.strip()]
    parsed: List[ParsedChanda] = []

    for comp in components:
        tokens = comp.split()
        norm_tokens = [normalize_label(t) for t in tokens]

        base_meter = None
        variants: List[str] = []
        deviation_label = None

        for tok in norm_tokens:
            if tok in BASE_METER_SYLLABLES:
                base_meter = tok
            elif tok in DEVIATION_LABELS:
                deviation_label = tok
            elif tok:
                variants.append(tok)

        parsed.append(
            ParsedChanda(
                raw=comp,
                base_meter=base_meter,
                variant_prefixes=variants,
                deviation_label=deviation_label,
                deviation_D=None,
            )
        )

    return parsed


def infer_deviation_label_from_D(D: int) -> Optional[str]:
    """
    Infer a deviation label purely from D, the difference between
    actual and base syllable counts.
    """
    if D == -1:
        return "nichrid"
    if D == 1:
        return "bhurik"
    if D == 2:
        return "viraj"
    if D >= 3:
        return "svaraj"
    return None


def compute_deviation_D(
    parsed: ParsedChanda, actual_syllables_per_pada: Optional[int]
) -> ParsedChanda:
    """
    Given a ParsedChanda and actual syllable count, compute D and attach.

    If base_meter or actual_syllables_per_pada is unknown, D stays None.

    If D is nonzero and parsed.deviation_label is missing, we infer a
    deviation label from D as per:

        D = actual - target
        -1 -> nichrid
        +1 -> bhurik
        +2 -> viraj
        >=3 -> svaraj
    """
    if parsed.base_meter is None or actual_syllables_per_pada is None:
        return parsed

    target = BASE_METER_SYLLABLES.get(parsed.base_meter)
    if target is None:
        return parsed

    D = actual_syllables_per_pada - target
    parsed.deviation_D = D

    if parsed.deviation_label is None:
        inferred = infer_deviation_label_from_D(D)
        if inferred is not None:
            parsed.deviation_label = inferred

    return parsed


if __name__ == "__main__":
    cell = "स्वराड् ब्राह्मी त्रिष्टुप्, याजुषी जगती"
    result = parse_chanda_cell(cell)
    for r in result:
        print(r)
    # Example numeric deviation usage
    r0 = compute_deviation_D(result[0], actual_syllables_per_pada=12)
    print("With deviation:", r0)
