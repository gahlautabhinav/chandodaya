# src/api.py

"""
api.py

Programmatic API entrypoints for the Vedic + Classical Sanskrit
Chandas Identification System.

Use these in your web backend / UI layer instead of directly calling
analyze_verse, when you want structured JSON-style data.

This version is:
    - Purely rule-based (no ML models).
    - Uses dataset_enriched to detect source_veda and padapatha.
    - Mirrors the logic of src/analyze_text.py but returns a dict.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from .normalization import normalize_text
from .pada_sandhi import split_padas
from .syllabifier import syllabify_line
from .svara_parser import detect_svara_for_akshara_text, svara_sequence_for_aksharas
from .feature_extractor import extract_features_for_mantra, mantra_features_to_dict
from .rule_based_classifier import classify_rule_based
from .padapatha_lookup import get_entry_for_text
from .padapatha import split_pratishakhya_padas

VEDIC_VEDAS = {"rigveda", "yajurveda", "samaveda", "atharvaveda"}


def analyze_text_to_dict(text_dev: str) -> Dict[str, Any]:
    """
    End-to-end analysis of a single Sanskrit text (Devanagari).

    This is the function your upstream input module should call
    once it has produced standardized Devanagari text.

    Parameters
    ----------
    text_dev : str
        Devanagari input (Saṁhitā or śloka), may contain Vedic svara marks.

    Returns
    -------
    dict
        JSON-serializable structure with:

        - input
        - normalization
        - samhita_padas
        - padapatha (if Vedic + present)
        - features (global)
        - meter_rule_based
    """
    # 0) Lookup in dataset_enriched, if available
    entry: Optional[Dict[str, Any]] = None
    try:
        entry = get_entry_for_text(text_dev)
    except Exception:
        entry = None

    if entry:
        detected_source_veda = str(entry.get("source_veda", "unknown")).lower()
        mantra_id = str(entry.get("id", "adhoc"))
        padapatha_text = entry.get("text_dev_padapatha")
        if isinstance(padapatha_text, str) and padapatha_text.strip():
            padapatha_text = padapatha_text.strip()
        else:
            padapatha_text = None
        chanda_raw = entry.get("meter_gold_raw")
        transliteration = entry.get("text_roman")
        veda_profile = entry.get("veda_profile", "adhoc")
        domain = entry.get("domain", "adhoc")
    else:
        detected_source_veda = "unknown"
        mantra_id = "adhoc"
        padapatha_text = None
        chanda_raw = None
        transliteration = None
        veda_profile = "adhoc"
        domain = "adhoc"

    # 1) Normalization (keep svaras for accent parsing)
    norm_with_svara = normalize_text(text_dev, strip_svaras=False)
    norm_no_svara = normalize_text(text_dev, strip_svaras=True)

    # 2) Saṁhitā pāda segmentation
    samhita_padas_struct: List[Dict[str, Any]] = []
    padas = split_padas(norm_with_svara)

    for p in padas:
        aksharas, LG, ganas = syllabify_line(p.text)
        ak_list = []
        svaras = svara_sequence_for_aksharas(aksharas)
        for idx, a in enumerate(aksharas, start=1):
            ak_list.append(
                {
                    "index": idx,
                    "text": a.text,
                    "vowel": a.vowel,
                    "coda": a.coda,
                    "prosodic_matra": a.prosodic_matra,
                    "phonetic_matra": a.phonetic_matra,
                    "L_or_G": a.L_or_G(),
                    "guru_reason": a.guru_reason,
                    "svara": svaras[idx - 1] if idx - 1 < len(svaras) else None,
                }
            )
        samhita_padas_struct.append(
            {
                "index": p.index + 1,
                "text": p.text,
                "LG": LG,
                "ganas": ganas,
                "aksharas": ak_list,
                "sandhi_profile": p.sandhi_profile,
            }
        )

    # 3) Padapāṭha analysis (if Vedic + padapatha_text present)
    padapatha_struct: Dict[str, Any] = {
        "raw": padapatha_text,
        "pratishakhya_padas": [],
    }
    if padapatha_text and detected_source_veda in VEDIC_VEDAS:
        pp_padas = split_pratishakhya_padas(padapatha_text)
        for pp in pp_padas:
            aksharas, LG_pp, ganas_pp = syllabify_line(pp.text)
            ak_list = []
            svaras_pp = svara_sequence_for_aksharas(aksharas)
            for idx, a in enumerate(aksharas, start=1):
                ak_list.append(
                    {
                        "index": idx,
                        "text": a.text,
                        "vowel": a.vowel,
                        "coda": a.coda,
                        "prosodic_matra": a.prosodic_matra,
                        "phonetic_matra": a.phonetic_matra,
                        "L_or_G": a.L_or_G(),
                        "guru_reason": a.guru_reason,
                        "svara": svaras_pp[idx - 1] if idx - 1 < len(svaras_pp) else None,
                    }
                )
            padapatha_struct["pratishakhya_padas"].append(
                {
                    "index": pp.index + 1,
                    "text": pp.text,
                    "LG": LG_pp,
                    "ganas": ganas_pp,
                    "aksharas": ak_list,
                }
            )

    # 4) Global features for meter classification
    feats = extract_features_for_mantra(
        mantra_id=mantra_id,
        source_veda=detected_source_veda,
        text_dev=text_dev,
        padapatha=padapatha_text,
        chanda_raw=chanda_raw,
        transliteration=transliteration,
        veda_profile=veda_profile,
        domain=domain,
    )
    feat_dict = mantra_features_to_dict(feats)

    # 5) Rule-based meter
    rb = classify_rule_based(
        pada_count=feat_dict["pada_count"],
        syllable_count_per_pada=feat_dict["syllable_count_per_pada"],
        source_veda=detected_source_veda,
    )

    meter_rule_based = {
        "base_family": rb.base_family,
        "deviation_D": rb.deviation_D,
        "deviation_label": rb.deviation_label,
        "full_label": rb.full_label,
        "notes": rb.notes,
    }

    return {
        "input": {
            "text_dev": text_dev,
            "detected_source_veda": detected_source_veda,
            "matched_id": mantra_id,
        },
        "normalization": {
            "with_svara": norm_with_svara,
            "without_svara": norm_no_svara,
        },
        "samhita_padas": samhita_padas_struct,
        "padapatha": padapatha_struct,
        "features": {
            "pada_count": feat_dict["pada_count"],
            "syllable_count_per_pada": feat_dict["syllable_count_per_pada"],
            "L_G_sequence": feat_dict["L_G_sequence"],
            "gana_sequence": feat_dict["gana_sequence"],
            "accent_pattern": feat_dict["accent_pattern"],
            "has_pluti": feat_dict["has_pluti"],
            "has_stobha": feat_dict["has_stobha"],
            "has_special_H": feat_dict["has_special_H"],
            "sandhi_profile": feat_dict["sandhi_profile"],
        },
        "meter_rule_based": meter_rule_based,
        # raw chandas label from dataset if present
        "meter_gold_raw": chanda_raw,
    }
