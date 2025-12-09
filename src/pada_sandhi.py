"""
pada_sandhi.py

Pāda segmentation and *lightweight* sandhi profiling.

Responsibilities
----------------
- Split a mantra string into pādas using danda markers
- Provide a simple sandhi profile (where syllable-final consonants
  merge with next pāda/word, affecting metrical vs orthographic count)

This is intentionally conservative: for a production-grade sandhi
analyzer, you'd plug in a full Sanskrit sandhi engine. Here we expose
hooks and a minimal heuristic profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Pada:
    """Representation of one pāda (metrical quarter)."""

    text: str
    index: int  # 0-based within verse
    sandhi_profile: Dict[str, int]  # simple counters


def split_padas(normalized_text: str) -> List[Pada]:
    """
    Split a normalized verse into pādas.

    Assumes:
    - danda normalization already performed: '|' for pāda, '||' for full-verse
    - input may or may not contain final '||'; we ignore it

    Parameters
    ----------
    normalized_text : str

    Returns
    -------
    List[Pada]
    """
    # Remove final '||' if present
    text = normalized_text.replace("||", "|")
    chunks = [c.strip() for c in text.split("|") if c.strip()]
    padas: List[Pada] = []
    for idx, chunk in enumerate(chunks):
        profile = compute_sandhi_profile(chunk)
        padas.append(Pada(text=chunk, index=idx, sandhi_profile=profile))
    return padas


def compute_sandhi_profile(pada_text: str) -> Dict[str, int]:
    """
    Very simple heuristic sandhi profile.

    We count:
    - word_final_visarga: appears as 'ः' before space or end
    - word_final_anusvara: 'ं' before space or end
    - internal_clusters: counts occurrences of consonant clusters (approx.)

    Parameters
    ----------
    pada_text : str

    Returns
    -------
    dict
    """
    profile = {
        "word_final_visarga": 0,
        "word_final_anusvara": 0,
        "internal_clusters": 0,
    }
    words = pada_text.split()
    for w in words:
        if w.endswith("ः"):
            profile["word_final_visarga"] += 1
        if w.endswith("ं"):
            profile["word_final_anusvara"] += 1
        # very crude cluster count: look for two non-vowel Devanagari letters in a row
        cluster_count = 0
        for i in range(len(w) - 1):
            if _is_consonant_like(w[i]) and _is_consonant_like(w[i + 1]):
                cluster_count += 1
        profile["internal_clusters"] += cluster_count

    return profile


def _is_consonant_like(ch: str) -> bool:
    # approximate; real implementation should share logic with syllabifier
    vowels = set("अआइईउऊऋॠऌॡएऐओऔािीुूृॄॢॣेैोौ")
    specials = set("ंःँ")
    if ch in vowels:
        return False
    if ch in specials:
        return False
    if ch.isspace():
        return False
    return True


if __name__ == "__main__":
    from src.normalization import normalize_text

    sample = "अग्निमीळे पुरोहितं | यज्ञस्य देवमृत्विजम् | होतारं रत्नधातमम् ||"
    norm = normalize_text(sample, strip_svaras=True)
    padas = split_padas(norm)
    for p in padas:
        print(p.index, repr(p.text), p.sandhi_profile)
