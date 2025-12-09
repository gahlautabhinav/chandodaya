# src/padapatha_lookup.py

"""
padapatha_lookup.py

Lookup padapāṭha (Padpath) and metadata for a given Devanagari Saṁhitā text,
using the enriched dataset (dataset_enriched.csv).
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any

import pandas as pd

from .normalization import normalize_text

_DATASET_CACHE: Optional[pd.DataFrame] = None


def _load_dataset_enriched() -> pd.DataFrame:
    global _DATASET_CACHE
    if _DATASET_CACHE is not None:
        return _DATASET_CACHE

    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, "data", "processed", "dataset_enriched.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"dataset_enriched.csv not found at {path}. "
            "Run `py -3.10 -m src.build_dataset` first."
        )

    df = pd.read_csv(path)

    if "text_dev_normalized" not in df.columns:
        raise ValueError("dataset_enriched.csv does not have 'text_dev_normalized' column")

    df["_norm_no_svara"] = df["text_dev_normalized"].astype(str).apply(
        lambda s: normalize_text(s, strip_svaras=True)
    )
    _DATASET_CACHE = df
    return df


def get_entry_for_text(text_dev: str) -> Optional[Dict[str, Any]]:
    df = _load_dataset_enriched()

    norm_with_svara = normalize_text(text_dev, strip_svaras=False)
    m = df[df["text_dev_normalized"] == norm_with_svara]
    if not m.empty:
        return m.iloc[0].to_dict()

    norm_no_svara = normalize_text(text_dev, strip_svaras=True)
    m2 = df[df["_norm_no_svara"] == norm_no_svara]
    if not m2.empty:
        return m2.iloc[0].to_dict()

    return None


def get_padapatha_for_text(text_dev: str) -> Optional[str]:
    entry = get_entry_for_text(text_dev)
    if not entry:
        return None
    val = entry.get("text_dev_padapatha")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None
