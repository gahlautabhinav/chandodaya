"""
build_chanda_rules.py

Build rule definitions for ALL unique chhandas in dataset_enriched.csv.

For each mantra, we construct a "full chanda label" from:
- meter_gold_base
- meter_variant_prefixes
- meter_deviation
- AND fallback to meter_gold_raw when base is missing.

For each full label, we compute:
- typical pāda_count
- typical syllable pattern per pāda
- base_family (most common meter_gold_base)
- max_diff_tolerance: maximum per-pāda syllable deviation seen for this label

These rules are written to:
    data/processed/chanda_rules.json

and then consumed by src/rule_based_classifier.py at inference time.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd

# Project directories
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RULES_JSON_PATH = os.path.join(PROCESSED_DIR, "chanda_rules.json")


def _parse_syllable_pattern(s: str) -> Optional[Tuple[int, ...]]:
    """
    Convert a string like "8,8,8,8" to a tuple (8, 8, 8, 8).
    Returns None if parsing fails.
    """
    if not s or not isinstance(s, str):
        return None
    parts = [p.strip() for p in s.split(",") if p.strip()]
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            return None
    return tuple(out)


def _build_full_chanda_label(row: pd.Series) -> Optional[str]:
    """
    Build a canonical "full chanda label" for a row.

    Priority:
    1. If meter_gold_base is present, combine:
       [meter_deviation] + meter_variant_prefixes + meter_gold_base
       e.g. "svaraj brahmi trishtubh"

    2. Else if meter_gold_raw is present, return that stripped.

    3. Else return None.
    """
    base = row.get("meter_gold_base")
    variants = row.get("meter_variant_prefixes")
    deviation = row.get("meter_deviation")
    raw = row.get("meter_gold_raw")

    if isinstance(base, str) and base.strip():
        parts = []
        if isinstance(deviation, str) and deviation.strip():
            parts.append(deviation.strip())
        if isinstance(variants, str) and variants.strip():
            parts.extend(variants.strip().split())
        parts.append(base.strip())
        return " ".join(parts)

    if isinstance(raw, str) and raw.strip():
        return raw.strip()

    return None


def build_chanda_rules(
    dataset_path: str,
    output_json: str,
    min_examples_per_label: int = 1,
) -> None:
    """
    Build chanda rules from dataset_enriched.csv and save as JSON.

    Parameters
    ----------
    dataset_path : str
        Path to data/processed/dataset_enriched.csv.
    output_json : str
        Path to data/processed/chanda_rules.json.
    min_examples_per_label : int
        Minimum number of examples required to create a rule for a label.
        Set to 1 to literally include all labels; raise to 3+ to ignore
        ultra-rare labels if desired.
    """
    df = pd.read_csv(dataset_path)

    # Construct full label
    df["full_label"] = df.apply(_build_full_chanda_label, axis=1)
    df = df.dropna(subset=["full_label"])

    # Compute parsed syllable pattern
    df["syll_pattern"] = df["syllable_count_per_pada"].apply(_parse_syllable_pattern)

    rules: List[Dict[str, Any]] = []

    grouped = df.groupby("full_label", dropna=True)

    for label, grp in grouped:
        total = len(grp)
        if total < min_examples_per_label:
            continue

        # Typical pāda_count
        try:
            pada_mode = int(grp["pada_count"].mode().iloc[0])
        except Exception:
            pada_mode = None

        # Patterns
        patterns = [p for p in grp["syll_pattern"].tolist() if p is not None]
        canonical_pattern: Optional[Tuple[int, ...]] = None
        max_diff_tolerance = 0

        if patterns:
            # Canonical pattern = most frequent pattern
            pattern_counts = Counter(patterns)
            canonical_pattern = pattern_counts.most_common(1)[0][0]

            # Compute maximum deviation from canonical
            diffs = []
            for pat in patterns:
                if len(pat) != len(canonical_pattern):
                    # length mismatch -> treat as large difference
                    diffs.append(max(len(pat), len(canonical_pattern)))
                    continue
                diffs.append(max(abs(a - b) for a, b in zip(pat, canonical_pattern)))
            if diffs:
                max_diff_tolerance = max(diffs)

        # Base family = most common meter_gold_base in this group
        base_fam = None
        if "meter_gold_base" in grp.columns:
            base_vals = [b for b in grp["meter_gold_base"].tolist() if isinstance(b, str) and b.strip()]
            if base_vals:
                base_counts = Counter(base_vals)
                base_fam = base_counts.most_common(1)[0][0]

        rules.append(
            {
                "label": label,
                "count": int(total),
                "pada_count": int(pada_mode) if pada_mode is not None else None,
                "syllable_pattern": list(canonical_pattern) if canonical_pattern is not None else None,
                "max_diff_tolerance": int(max_diff_tolerance),
                "base_family": base_fam,
            }
        )

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(rules)} chanda rules to {output_json}")


if __name__ == "__main__":
    dataset_path = os.path.join(PROCESSED_DIR, "dataset_enriched.csv")
    build_chanda_rules(dataset_path, RULES_JSON_PATH, min_examples_per_label=1)
