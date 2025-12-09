"""
api.py

Programmatic API entrypoints for the Vedic + Classical Sanskrit
Chandas Identification System.

Use these in your web backend / CLI wrapper / UI layer instead of
directly calling analyze_verse, when you want structured data instead
of printed tables.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from .normalization import normalize_text
from .pada_sandhi import split_padas
from .syllabifier import syllabify_line
from .feature_extractor import extract_features_for_mantra, mantra_features_to_dict
from .model_utils import (
    load_model,
    features_to_model_input,
    BASELINE_MODEL_NAME,
    MLP_MODEL_NAME,
)


def analyze_text_to_dict(
    text_dev: str,
    assumed_source_veda: str = "unknown",
) -> Dict[str, Any]:
    """
    End-to-end analysis of a single Sanskrit text (Devanagari).

    This is the function your upstream input module should call
    once it has produced standardized Devanagari text.

    Parameters
    ----------
    text_dev : str
        Standardized Devanagari input.
    assumed_source_veda : str, default "unknown"
        Hint for the classifier: "rigveda", "yajurveda", "samaveda", or "unknown".

    Returns
    -------
    dict
        JSON-serializable structure with:
        - "input"
        - "normalized"
        - "padas"    : list of {"index", "text", "aksharas", "LG", "ganas", ...}
        - "features" : global features (pada_count, L_G_sequence, ...)
        - "meter"    : predictions from available models
    """
    # 1) Normalize (svara-stripped for counting)
    norm = normalize_text(text_dev, strip_svaras=True)

    # 2) Pāda segmentation
    padas_struct: List[Dict[str, Any]] = []
    padas = split_padas(norm)

    for p in padas:
        aksharas, LG, ganas = syllabify_line(p.text)
        ak_list = []
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
                }
            )
        padas_struct.append(
            {
                "index": p.index,
                "text": p.text,
                "LG": LG,
                "ganas": ganas,
                "aksharas": ak_list,
                "sandhi_profile": p.sandhi_profile,
            }
        )

    # 3) Global features (same as for training)
    feats = extract_features_for_mantra(
        mantra_id="adhoc",
        source_veda=assumed_source_veda,
        text_dev=text_dev,
        padapatha=None,
        chanda_raw=None,
        transliteration=None,
        veda_profile="adhoc",
        domain="adhoc",
    )
    feat_dict = mantra_features_to_dict(feats)

    # 4) Meter predictions (baseline + MLP if available)
    meter_info: Dict[str, Any] = {}

    # Baseline
    baseline_model = load_model(BASELINE_MODEL_NAME)
    if baseline_model is not None:
        X_baseline = features_to_model_input(feats, override_source_veda=assumed_source_veda)
        pred_base = baseline_model.predict(X_baseline)[0]
        meter_info["baseline"] = pred_base

    # MLP
    mlp_model = load_model(MLP_MODEL_NAME)
    if mlp_model is not None:
        X_mlp = features_to_model_input(feats, override_source_veda=assumed_source_veda)
        pred_mlp = mlp_model.predict(X_mlp)[0]
        meter_info["mlp"] = pred_mlp

    return {
        "input": {
            "text_dev": text_dev,
            "assumed_source_veda": assumed_source_veda,
        },
        "normalized": norm,
        "padas": padas_struct,
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
        "meter": meter_info,
    }
