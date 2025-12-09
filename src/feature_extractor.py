"""
feature_extractor.py

End-to-end feature extraction for a single mantra / verse.

Purely data-driven:
    - syllable_count_per_pada is taken directly from the syllabifier output,
      no canonical Vedic pattern override.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from typing import Optional, List, Dict, Any

from .normalization import normalize_text
from .pada_sandhi import split_padas
from .syllabifier import syllabify_line, Akshara
from .svara_parser import svara_sequence_for_aksharas


@dataclass
class MantraFeatures:
    id: str
    source_veda: str
    veda_profile: str
    domain: str

    text_dev_original: str
    text_dev_normalized: str
    text_dev_padapatha: Optional[str]
    text_roman: Optional[str]

    meter_gold_raw: Optional[str]

    pada_count: int
    syllable_count_per_pada: str
    L_G_sequence: str
    gana_sequence: str
    accent_pattern: str

    has_pluti: bool
    has_stobha: bool
    has_special_H: bool

    sandhi_profile: str


PLUTI_MARKERS = ["३"]
STOBHA_PARTICLES = ["हो", "हि", "है", "हौ", "ओ", "आइ", "इउ", "हु", "हे", "हा"]
SPECIAL_H_SIGNS = ["\u1CF2", "\u1CF3"]


def detect_pluti(text: str) -> bool:
    return any(m in text for m in PLUTI_MARKERS)


def detect_stobha(text: str) -> bool:
    return any(p in text for p in STOBHA_PARTICLES)


def detect_special_H(text: str) -> bool:
    return any(h in text for h in SPECIAL_H_SIGNS)


def extract_features_for_mantra(
    mantra_id: str,
    source_veda: str,
    text_dev: str,
    padapatha: Optional[str],
    chanda_raw: Optional[str],
    transliteration: Optional[str],
    veda_profile: str,
    domain: str,
) -> MantraFeatures:
    text_dev_original = text_dev

    # 1) Normalize, keep svaras
    norm = normalize_text(text_dev_original, strip_svaras=False)

    # 2) Saṁhitā pāda segmentation
    padas = split_padas(norm)
    pada_count = len(padas)

    syllable_counts: List[int] = []
    LG_chunks: List[str] = []
    gana_chunks: List[str] = []
    svara_chunks: List[str] = []
    sandhi_profiles: List[Dict[str, Any]] = []

    for p in padas:
        aksharas, LG, ganas = syllabify_line(p.text)
        syllable_counts.append(len(aksharas))
        LG_chunks.append(LG)
        gana_chunks.append("-".join(ganas))

        svaras = svara_sequence_for_aksharas(aksharas)
        svara_chunks.append(",".join(svaras))

        sandhi_profiles.append(p.sandhi_profile)

    syllable_count_per_pada = ",".join(str(c) for c in syllable_counts)
    L_G_sequence = " | ".join(LG_chunks)
    gana_sequence = " || ".join(gana_chunks)
    accent_pattern = " || ".join(svara_chunks)

    has_pluti = detect_pluti(norm)
    has_stobha = detect_stobha(norm)
    has_special_H = detect_special_H(norm)

    sandhi_profile_str = json.dumps(sandhi_profiles, ensure_ascii=False)

    return MantraFeatures(
        id=mantra_id,
        source_veda=source_veda,
        veda_profile=veda_profile,
        domain=domain,
        text_dev_original=text_dev_original,
        text_dev_normalized=norm,
        text_dev_padapatha=padapatha,
        text_roman=transliteration,
        meter_gold_raw=chanda_raw,
        pada_count=pada_count,
        syllable_count_per_pada=syllable_count_per_pada,
        L_G_sequence=L_G_sequence,
        gana_sequence=gana_sequence,
        accent_pattern=accent_pattern,
        has_pluti=has_pluti,
        has_stobha=has_stobha,
        has_special_H=has_special_H,
        sandhi_profile=sandhi_profile_str,
    )


def mantra_features_to_dict(feats: MantraFeatures) -> Dict[str, Any]:
    return asdict(feats)
