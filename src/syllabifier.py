"""
syllabifier.py

Akṣara segmentation + mātrā + L/G + gaṇa computation.

Pipeline for one pāda:
    text -> [Akshara] -> L/G string -> Pingala gaṇas (triplets)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# --- Devanagari categories (simplified) ---

INDEPENDENT_VOWELS = set("अआइईउऊऋॠऌॡएऐओऔॐ")
DEPENDENT_VOWEL_SIGNS = set("ािीुूृॄॢॣेैोौॅॉॆॊ")
ANUSVARA = "ं"
VISARGA = "ः"
CANDRABINDU = "ँ"
NUKTA = "़"

CONSONANTS = set(
    "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"
)

# Pingala gaṇa mapping (G = guru, L = laghu)
GANA_MAP = {
    "LLL": "na",
    "LLG": "ya",
    "LGL": "ta",
    "LGG": "ra",
    "GLL": "ma",
    "GLG": "bha",
    "GGL": "sa",
    "GGG": "ja",
}


@dataclass
class Akshara:
    text: str
    vowel: str
    coda: str
    prosodic_matra: int
    phonetic_matra: int
    guru_reason: str = ""

    def L_or_G(self) -> str:
        return "G" if self.prosodic_matra >= 2 else "L"


def _is_independent_vowel(ch: str) -> bool:
    return ch in INDEPENDENT_VOWELS


def _is_dependent_vowel(ch: str) -> bool:
    return ch in DEPENDENT_VOWEL_SIGNS


def _is_consonant(ch: str) -> bool:
    return ch in CONSONANTS


def _is_mark(ch: str) -> bool:
    return ch in {ANUSVARA, VISARGA, CANDRABINDU, NUKTA}


def _matra_for_vowel(v: str) -> int:
    """
    Prosodic mātrā (simplified):

    Short: 1  (अ इ उ ऋ ऌ + their short signs)
    Long : 2  (आ ई ऊ ॠ ॡ ए ऐ ओ औ + long signs)
    """
    short = set("अइउऋऌिुृॢ")
    long = set("आईऊॠॡएऐओऔाीूॄॣेैोौ")

    if v in long:
        return 2
    if v in short:
        return 1
    return 1


def lg_to_ganas(lg: str) -> List[str]:
    """
    Convert an L/G pattern (string) into Pingala gaṇas.

    - Group syllables in triplets from left to right.
    - Leftover 1–2 syllables at end are ignored for gaṇa naming.
    """
    lg = lg.replace(" ", "").strip()
    ganas: List[str] = []
    n = len(lg)
    usable = n - (n % 3)
    for i in range(0, usable, 3):
        triplet = lg[i : i + 3]
        name = GANA_MAP.get(triplet, "?")
        ganas.append(name)
    return ganas


def syllabify_line(text: str) -> tuple[List[Akshara], str, List[str]]:
    """
    Segment a Devanagari line into akṣaras, compute mātrās, L/G, and gaṇas.

    Algorithm:
    ----------
    - New akṣara starts at:
        * independent vowel
        * consonant when there is no current akṣara (implicit 'अ')
    - Dependent vowel signs attach to the current akṣara's vowel.
    - Following consonants / anusvara / visarga / candrabindu attach as coda.
    - Whitespace and danda signs flush current akṣara.
    """
    aksharas: List[Akshara] = []

    cur_text: List[str] = []
    cur_vowel: Optional[str] = None
    cur_coda: List[str] = []

    def flush_current():
        nonlocal cur_text, cur_vowel, cur_coda
        if not cur_text and not cur_vowel and not cur_coda:
            return
        full_text = "".join(cur_text + cur_coda)
        vowel = cur_vowel or "अ"
        coda = "".join(cur_coda)

        pros = _matra_for_vowel(vowel)
        if coda:
            pros = max(pros, 2)
            guru_reason = "coda_cluster"
        elif pros >= 2:
            guru_reason = "long_vowel"
        else:
            guru_reason = "short_open"

        aksharas.append(
            Akshara(
                text=full_text,
                vowel=vowel,
                coda=coda,
                prosodic_matra=pros,
                phonetic_matra=pros,
                guru_reason=guru_reason,
            )
        )
        cur_text = []
        cur_vowel = None
        cur_coda = []

    chars = list(text)
    n = len(chars)
    i = 0

    while i < n:
        ch = chars[i]

        if ch.isspace() or ch in "|।॥":
            flush_current()
            i += 1
            continue

        if _is_independent_vowel(ch):
            flush_current()
            cur_text = [ch]
            cur_vowel = ch
            cur_coda = []
            i += 1
            continue

        if _is_consonant(ch):
            if not cur_text and cur_vowel is None:
                cur_text = [ch]
                cur_vowel = "अ"
                cur_coda = []
            else:
                cur_text.append(ch)
            i += 1
            continue

        if _is_dependent_vowel(ch):
            if not cur_text:
                flush_current()
                cur_text = [ch]
                cur_vowel = ch
                cur_coda = []
            else:
                cur_text.append(ch)
                cur_vowel = ch
            i += 1
            continue

        if _is_mark(ch):
            cur_coda.append(ch)
            i += 1
            continue

        cur_text.append(ch)
        i += 1

    flush_current()

    LG = "".join(a.L_or_G() for a in aksharas)
    ganas = lg_to_ganas(LG)

    return aksharas, LG, ganas


if __name__ == "__main__":
    line = "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्"
    aks, LG, ganas = syllabify_line(line)
    for idx, a in enumerate(aks, start=1):
        print(idx, a.text, a.vowel, a.coda, a.prosodic_matra, a.L_or_G(), a.guru_reason)
    print("L/G:", LG)
    print("Gaṇas:", ganas)
