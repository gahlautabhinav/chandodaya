"""
rule_based_classifier.py

Rule-based meter classifier extended to ALL unique chhandas found in
data/processed/dataset_enriched.csv via chanda_rules.json.

Two layers:
-----------
1) Data-derived rules from chanda_rules.json
   - label
   - pada_count
   - canonical syllable_pattern
   - max_diff_tolerance
   - base_family (if known)

2) Fallback Pingala rules for the 7 major Vedic chandas:
   - gayatri, ushnih, anushtubh, brihati, pankti, trishtubh, jagati

We always try layer (1) first. If no rule matches well enough, we
fall back to layer (2).

Deviation system:
-----------------
D = first_pada_syllables - target_for_family
-1 -> nichrid
+1 -> bhurik
+2 -> viraj
>=3 -> svaraj
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple


# Project root + data
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RULES_JSON_PATH = os.path.join(PROCESSED_DIR, "chanda_rules.json")


# Target syllables per pāda for Pingala 7
BASE_METER_SYLLABLES = {
    "gayatri": 8,
    "ushnih": 7,
    "anushtubh": 8,
    "brihati": 9,
    "pankti": 8,
    "trishtubh": 11,
    "jagati": 12,
}


@dataclass
class RuleBasedResult:
    base_family: Optional[str]
    deviation_D: Optional[int]
    deviation_label: Optional[str]
    full_label: Optional[str]
    notes: List[str]


def _parse_counts(s: str) -> List[int]:
    """
    Parse syllable_count_per_pada string like "8,8,8,8" -> [8, 8, 8, 8].
    """
    if not s:
        return []
    parts = [p.strip() for p in str(s).split(",") if p.strip()]
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            continue
    return out


def _infer_deviation_label(D: int) -> Optional[str]:
    """
    Map D to deviation label.
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


# ==========================
# Layer 1: Data-derived rules
# ==========================

def _load_chanda_rules() -> List[Dict[str, Any]]:
    if not os.path.exists(RULES_JSON_PATH):
        return []
    with open(RULES_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CHANDA_RULES: List[Dict[str, Any]] = _load_chanda_rules()


def _match_chanda_rule(
    pada_count: int,
    counts: List[int],
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Try to match the given pattern against chanda_rules.json.

    Strategy:
    ---------
    - Consider only rules with same `pada_count`.
    - Require rule.syllable_pattern to exist and have same length as counts.
    - Compute max_abs_diff = max |c_i - r_i|.
      - If max_abs_diff <= max_diff_tolerance, rule is a candidate.
    - Prefer the candidate with:
      - smallest max_abs_diff
      - then largest rule["count"] (more support)
    """
    notes: List[str] = []
    if not CHANDA_RULES:
        notes.append("No chanda_rules.json loaded; skipping data-derived rules.")
        return None, notes

    notes.append(f"Trying to match {pada_count} pādas with counts {counts} against {len(CHANDA_RULES)} rules.")

    best_rule = None
    best_score = None
    best_support = None

    for rule in CHANDA_RULES:
        rule_pada = rule.get("pada_count")
        rule_pattern = rule.get("syllable_pattern")
        tol = rule.get("max_diff_tolerance", 0)
        cnt = rule.get("count", 0)

        if rule_pada is None or rule_pattern is None:
            continue
        if rule_pada != pada_count:
            continue
        if len(rule_pattern) != len(counts):
            continue

        max_abs_diff = max(abs(c - r) for c, r in zip(counts, rule_pattern))

        # accept only if within tolerance
        if max_abs_diff > tol:
            continue

        # smaller difference is better; break ties by larger count (support)
        if best_score is None or max_abs_diff < best_score or (
            max_abs_diff == best_score and cnt > (best_support or 0)
        ):
            best_score = max_abs_diff
            best_support = cnt
            best_rule = rule

    if best_rule is None:
        notes.append("No matching data-derived chanda rule found.")
    else:
        notes.append(
            f"Matched data-derived rule: label='{best_rule['label']}' "
            f"pattern={best_rule['syllable_pattern']} tol={best_rule['max_diff_tolerance']} "
            f"(support={best_rule['count']}, max_abs_diff={best_score})."
        )

    return best_rule, notes


# ==========================
# Layer 2: Pingala fallback
# ==========================

def _choose_base_family_pingala(
    pada_count: int,
    counts: List[int],
) -> Tuple[Optional[str], List[str]]:
    """
    Decide base family from pāda_count and syllable counts, using only
    Pingala 7 heuristic.
    """
    notes: List[str] = []

    if not counts:
        notes.append("No syllable counts available.")
        return None, notes

    first = counts[0]
    all_equal = len(set(counts)) == 1

    if all_equal:
        n = first
        if pada_count == 3 and n == 8:
            notes.append("Pingala: 3 pādas x 8 syll -> gayatri")
            return "gayatri", notes
        if pada_count == 4 and n == 8:
            notes.append("Pingala: 4 pādas x 8 syll -> anushtubh")
            return "anushtubh", notes
        if pada_count == 5 and n == 8:
            notes.append("Pingala: 5 pādas x 8 syll -> pankti")
            return "pankti", notes
        if pada_count == 4 and n == 11:
            notes.append("Pingala: 4 pādas x 11 syll -> trishtubh")
            return "trishtubh", notes
        if pada_count == 4 and n == 12:
            notes.append("Pingala: 4 pādas x 12 syll -> jagati")
            return "jagati", notes
        if pada_count == 4 and n == 9:
            notes.append("Pingala: 4 pādas x 9 syll -> brihati")
            return "brihati", notes
        if 2 <= pada_count <= 4 and n == 7:
            notes.append("Pingala: 2-4 pādas x 7 syll -> ushnih")
            return "ushnih", notes

    # If not perfect, choose closest target by |D|
    best_family = None
    best_D_abs = None
    for fam, target in BASE_METER_SYLLABLES.items():
        D = first - target
        if best_D_abs is None or abs(D) < best_D_abs:
            best_D_abs = abs(D)
            best_family = fam

    if best_family is not None:
        notes.append(
            f"Pingala fallback: picked {best_family} as closest to first pāda count {first}."
        )
    else:
        notes.append("Pingala fallback: no base family determined.")
    return best_family, notes


# ==========================
# Public API
# ==========================

def classify_rule_based(
    pada_count: int,
    syllable_count_per_pada: str,
    source_veda: str = "unknown",
) -> RuleBasedResult:
    """
    Extended rule-based meter classifier.

    1) Try data-derived rules from chanda_rules.json:
        - full_label = label from rules file
        - base_family = rule["base_family"] if present
    2) If no rule matches, fall back to Pingala 7 heuristic.

    Deviation D is always computed relative to base_family if known.
    """
    counts = _parse_counts(syllable_count_per_pada)
    notes: List[str] = []
    notes.append(f"Parsed syllable counts per pāda: {counts}")
    notes.append(f"Pāda count: {pada_count}, source_veda: {source_veda}")

    # Layer 1: data-derived rules
    rule, rule_notes = _match_chanda_rule(pada_count, counts)
    notes.extend(rule_notes)

    full_label = None
    base_family = None

    if rule is not None:
        full_label = rule.get("label")
        base_family = rule.get("base_family")
        if base_family:
            notes.append(f"Using base_family from rule: {base_family}")
        else:
            notes.append("Rule has no base_family; will rely on Pingala for family if needed.")

    # If no rule or rule has no base_family, use Pingala fallback to guess family
    if base_family is None:
        ping_fam, ping_notes = _choose_base_family_pingala(pada_count, counts)
        notes.extend(ping_notes)
        base_family = ping_fam

    # If after all this we still have no base family or counts, we can't compute D
    if base_family is None or not counts:
        return RuleBasedResult(
            base_family=None,
            deviation_D=None,
            deviation_label=None,
            full_label=full_label,
            notes=notes,
        )

    target = BASE_METER_SYLLABLES.get(base_family)
    if target is None:
        # Unknown family in BASE_METER_SYLLABLES; just return label
        notes.append(f"Base family '{base_family}' not in Pingala 7 map; skipping deviation D.")
        return RuleBasedResult(
            base_family=base_family,
            deviation_D=None,
            deviation_label=None,
            full_label=full_label or base_family,
            notes=notes,
        )

    first = counts[0]
    D = first - target
    dev_label = _infer_deviation_label(D)
    if dev_label is None:
        notes.append(f"D = {D} -> no deviation label (exact or minor).")
        final_label = full_label or base_family
    else:
        notes.append(f"D = {D} -> deviation label = {dev_label}.")
        # If full_label already contains something, keep it; else compose
        final_label = full_label or f"{dev_label} {base_family}"

    return RuleBasedResult(
        base_family=base_family,
        deviation_D=D,
        deviation_label=dev_label,
        full_label=final_label,
        notes=notes,
    )


if __name__ == "__main__":
    # Smoke test
    examples = [
        (3, "8,8,8", "rigveda"),
        (4, "8,8,8,8", "classical"),
        (4, "11,11,11,11", "rigveda"),
        (4, "12,12,12,12", "rigveda"),
    ]
    for pc, sc, veda in examples:
        res = classify_rule_based(pc, sc, veda)
        print("\nInput:", pc, sc, veda)
        print("Base family:", res.base_family)
        print("Deviation D:", res.deviation_D)
        print("Deviation label:", res.deviation_label)
        print("Full label:", res.full_label)
        print("Notes:", *res.notes, sep="\n  - ")
