# src/analyze_text.py

from __future__ import annotations

from typing import Any, Dict

from tabulate import tabulate

from .normalization import normalize_text
from .pada_sandhi import split_padas
from .syllabifier import syllabify_line
from .svara_parser import detect_svara_for_akshara_text
from .rule_based_classifier import classify_rule_based
from .feature_extractor import extract_features_for_mantra, mantra_features_to_dict
from .padapatha_lookup import get_entry_for_text
from .padapatha import split_pratishakhya_padas

VEDIC_VEDAS = {"rigveda", "yajurveda", "samaveda", "atharvaveda"}


def analyze_verse(text: str) -> None:
    """
    Analyze a single verse/mantra:

    - Auto-detect source_veda from dataset_enriched (if present)
    - Normalize
    - Saṁhitā pāda segmentation
    - Akṣara / L-G / gaṇa per Saṁhitā pāda
    - For Vedic mantras: padapāṭha → Prātiśākhya padas (from dataset)
    - Rule-based meter classification
    - Summary features
    """
    print("=== Raw input ===")
    print(text)
    print()

    # 0) Try to identify this mantra in dataset_enriched
    entry: Dict[str, Any] | None = None
    try:
        entry = get_entry_for_text(text)
    except Exception:
        entry = None

    if entry:
        detected_source_veda = str(entry.get("source_veda", "unknown")).lower()
        print(f"Detected source_veda from dataset: {detected_source_veda}")
    else:
        detected_source_veda = "unknown"
        print("No matching entry in dataset_enriched; treating as 'unknown' / classical.")
    print()

    # 1) Normalize (keep svaras for accent parsing)
    norm = normalize_text(text, strip_svaras=False)
    print("=== Normalized (svara-kept, danda-normalized) ===")
    print(norm)
    print()

    # 2) Saṁhitā pāda segmentation
    padas = split_padas(norm)
    print("=== Pāda segmentation (Saṁhitā) ===")
    for p in padas:
        print(f"Pāda {p.index+1}: {p.text}")
    print()

    # 3) Akṣaras / L/G / gaṇas for Saṁhitā pādas
    for p in padas:
        aksharas, LG, ganas = syllabify_line(p.text)
        rows = []
        for idx, a in enumerate(aksharas, start=1):
            svara = detect_svara_for_akshara_text(a.text)
            rows.append(
                [
                    idx,
                    a.text,
                    a.vowel,
                    a.coda,
                    a.prosodic_matra,
                    a.L_or_G(),
                    a.guru_reason,
                    svara,
                ]
            )
        print(f"=== Akṣaras for Saṁhitā pāda {p.index+1} ===")
        print(
            tabulate(
                rows,
                headers=["#", "akṣara", "vowel", "coda", "mātrā", "L/G", "guru_reason", "svara"],
                tablefmt="psql",
            )
        )
        print("L/G pattern:", LG)
        print("Gaṇas:", "-".join(ganas))
        print()

    # 4) For Vedic mantras: padapāṭha → Prātiśākhya segmentation (from dataset)
    padapatha_text: str | None = None
    if entry and detected_source_veda in VEDIC_VEDAS:
        val = entry.get("text_dev_padapatha")
        if isinstance(val, str) and val.strip():
            padapatha_text = val.strip()

    if padapatha_text and detected_source_veda in VEDIC_VEDAS:
        print("=== Padapāṭha (from dataset_enriched) ===")
        print(padapatha_text)
        print()

        pp_padas = split_pratishakhya_padas(padapatha_text)
        print("=== Prātiśākhya padas from Padapāṭha ===")
        for pp in pp_padas:
            print(f"Pada {pp.index+1}: {pp.text}")
        print()

        for pp in pp_padas:
            aksharas, LG_pp, ganas_pp = syllabify_line(pp.text)
            rows = []
            for idx, a in enumerate(aksharas, start=1):
                svara = detect_svara_for_akshara_text(a.text)
                rows.append(
                    [
                        idx,
                        a.text,
                        a.vowel,
                        a.coda,
                        a.prosodic_matra,
                        a.L_or_G(),
                        a.guru_reason,
                        svara,
                    ]
                )
            print(f"=== Akṣaras for padapāṭha-pada {pp.index+1} ===")
            print(
                tabulate(
                    rows,
                    headers=["#", "akṣara", "vowel", "coda", "mātrā", "L/G", "guru_reason", "svara"],
                    tablefmt="psql",
                )
            )
            print("L/G pattern:", LG_pp)
            print("Gaṇas:", "-".join(ganas_pp))
            print()
    else:
        print("No usable padapāṭha (either not Vedic or not found).")
        print()

    # 5) Full feature extraction (for rule-based meter)
    feats = extract_features_for_mantra(
        mantra_id=str(entry.get("id", "adhoc")) if entry else "adhoc",
        source_veda=detected_source_veda,
        text_dev=text,
        padapatha=padapatha_text,
        chanda_raw=entry.get("meter_gold_raw") if entry else None,
        transliteration=entry.get("text_roman") if entry else None,
        veda_profile=entry.get("veda_profile", "adhoc") if entry else "adhoc",
        domain=entry.get("domain", "adhoc") if entry else "adhoc",
    )
    feat_dict = mantra_features_to_dict(feats)

    # 6) Rule-based meter classification
    print("=== Rule-based meter classification ===")
    rb = classify_rule_based(
        pada_count=feat_dict["pada_count"],
        syllable_count_per_pada=feat_dict["syllable_count_per_pada"],
        source_veda=detected_source_veda,
    )
    print("Base family:", rb.base_family)
    print("Deviation D:", rb.deviation_D)
    print("Deviation label:", rb.deviation_label)
    print("Full rule-based label:", rb.full_label)
    print("Notes:")
    for note in rb.notes:
        print("  -", note)
    print()

    # 7) Summary features
    print("=== Summary features ===")
    summary_rows = [
        ("pada_count", feat_dict["pada_count"]),
        ("syllable_count_per_pada", feat_dict["syllable_count_per_pada"]),
        ("L_G_sequence", feat_dict["L_G_sequence"]),
        ("gana_sequence", feat_dict["gana_sequence"]),
        ("accent_pattern", feat_dict["accent_pattern"]),
        ("has_pluti", feat_dict["has_pluti"]),
        ("has_stobha", feat_dict["has_stobha"]),
        ("has_special_H", feat_dict["has_special_H"]),
    ]
    print(tabulate(summary_rows, headers=["feature", "value"], tablefmt="psql"))
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Sanskrit verse/mantra for chandas (rule-based).")
    parser.add_argument("text", help="Devanagari verse text (Saṁhitā or śloka).")

    args = parser.parse_args()
    analyze_verse(args.text)
