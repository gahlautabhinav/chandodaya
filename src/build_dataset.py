"""
build_dataset.py

Combine Rigveda, Yajurveda, Samaveda CSVs into a single enriched dataset
with metrical features and parsed chanda labels.

Expected input CSV schemas (flexible)
-------------------------------------
Rigveda.csv: columns include at least:
    - 'Mandal', 'Sukta', 'Mantra Number'
    - mantra text: 'MantraText' OR 'Mantra'
    - 'Chanda'
    - 'Padpath' (optional)
    - 'Transliteration' (optional)

Yajurveda.csv:
    - 'Adhyay', 'Mantra Number'
    - 'Mantra'
    - 'Chanda'
    - 'Padpath' (optional)

Samveda.csv:
    - 'Mantra Number'
    - 'Mantra'
    - 'Chanda'
    - 'Padpath' (optional)

Output schema (columns)
-----------------------
id, source_veda, veda_profile, domain,
text_dev_original, text_dev_normalized, text_dev_padapatha, text_roman,
meter_gold_raw, meter_gold_base, meter_variant_prefixes, meter_deviation,
deviation_vector,
pada_count, syllable_count_per_pada, L_G_sequence, gana_sequence,
accent_pattern, has_pluti, has_stobha, has_special_H, sandhi_profile
"""

from __future__ import annotations

import os
from typing import List, Any, Iterable

import pandas as pd

from .feature_extractor import extract_features_for_mantra, mantra_features_to_dict
from .chanda_parser import parse_chanda_cell, compute_deviation_D

# Project-relative data directory (vedic-chandas/data)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _rigveda_id(row) -> str:
    """Rigveda ID format: RV-Mandal.Sukta.MantraNumber (e.g. RV-1.1.1)"""
    return f"RV-{row['Mandal']}.{row['Sukta']}.{row['Mantra Number']}"


def _yajurveda_id(row) -> str:
    """Yajurveda ID format: YV-Adhyay.MantraNumber (e.g. YV-1.1)"""
    return f"YV-{row['Adhyay']}.{row['Mantra Number']}"


def _samaveda_id(row) -> str:
    """Samaveda ID format: SV-MantraNumber (e.g. SV-2)"""
    return f"SV-{row['Mantra Number']}"


def _get_first_existing(row, candidates: Iterable[str], default: Any = "") -> Any:
    """
    Safe helper: from a pandas Series (row), return the first column that exists
    among `candidates`. If none exist, return `default`.
    """
    for name in candidates:
        if name in row.index:
            return row[name]
    return default


def build_enriched_dataset(
    rig_csv: str,
    yaj_csv: str,
    sama_csv: str,
    output_csv: str,
) -> None:
    """
    Main entrypoint: read three CSVs, compute features, write combined CSV.

    Parameters
    ----------
    rig_csv, yaj_csv, sama_csv : str
        Paths to input CSVs (Rigveda.csv / Yajurveda.csv / Samveda.csv).
    output_csv : str
        Path for enriched CSV.
    """
    rows: List[dict] = []

    # --- Rigveda ---
    rig_df = pd.read_csv(rig_csv)
    for _, r in rig_df.iterrows():
        mantra_id = _rigveda_id(r)

        # Text column: try 'MantraText' first, then 'Mantra'
        text_dev = str(_get_first_existing(r, ["MantraText", "Mantra"]))

        padpath = _get_first_existing(r, ["Padpath", "PadPath"], default=None)
        chanda_raw = _get_first_existing(r, ["Chanda"], default=None)
        translit = _get_first_existing(r, ["Transliteration"], default=None)

        feats = extract_features_for_mantra(
            mantra_id=mantra_id,
            source_veda="rigveda",
            text_dev=text_dev,
            padapatha=padpath,
            chanda_raw=chanda_raw,
            transliteration=translit,
            veda_profile="rig_shakala",
            domain="samhita",
        )
        feat_dict = mantra_features_to_dict(feats)

        # Parse chanda and compute deviation based on first pāda syllable count
        parsed_list = parse_chanda_cell(chanda_raw or "")
        if parsed_list:
            parsed = parsed_list[0]  # global/base meter
            try:
                first_pada_syllables = int(
                    str(feat_dict["syllable_count_per_pada"]).split(",")[0]
                )
            except Exception:
                first_pada_syllables = None
            parsed = compute_deviation_D(parsed, first_pada_syllables)

            feat_dict["meter_gold_base"] = parsed.base_meter
            feat_dict["meter_variant_prefixes"] = " ".join(parsed.variant_prefixes)
            feat_dict["meter_deviation"] = parsed.deviation_label
            feat_dict["deviation_vector"] = (
                "" if parsed.deviation_D is None else str(parsed.deviation_D)
            )

        rows.append(feat_dict)

    # --- Yajurveda ---
    yaj_df = pd.read_csv(yaj_csv)
    for _, r in yaj_df.iterrows():
        mantra_id = _yajurveda_id(r)

        text_dev = str(_get_first_existing(r, ["MantraText", "Mantra"]))
        padpath = _get_first_existing(r, ["Padpath", "PadPath"], default=None)
        chanda_raw = _get_first_existing(r, ["Chanda"], default=None)

        feats = extract_features_for_mantra(
            mantra_id=mantra_id,
            source_veda="yajurveda",
            text_dev=text_dev,
            padapatha=padpath,
            chanda_raw=chanda_raw,
            transliteration=None,
            veda_profile="yaj_madhyandina",  # adjust if needed
            domain="samhita",
        )
        feat_dict = mantra_features_to_dict(feats)

        parsed_list = parse_chanda_cell(chanda_raw or "")
        if parsed_list:
            parsed = parsed_list[0]
            try:
                first_pada_syllables = int(
                    str(feat_dict["syllable_count_per_pada"]).split(",")[0]
                )
            except Exception:
                first_pada_syllables = None
            parsed = compute_deviation_D(parsed, first_pada_syllables)
            feat_dict["meter_gold_base"] = parsed.base_meter
            feat_dict["meter_variant_prefixes"] = " ".join(parsed.variant_prefixes)
            feat_dict["meter_deviation"] = parsed.deviation_label
            feat_dict["deviation_vector"] = (
                "" if parsed.deviation_D is None else str(parsed.deviation_D)
            )

        rows.append(feat_dict)

    # --- Samaveda ---
    sama_df = pd.read_csv(sama_csv)
    for _, r in sama_df.iterrows():
        mantra_id = _samaveda_id(r)

        text_dev = str(_get_first_existing(r, ["MantraText", "Mantra"]))
        padpath = _get_first_existing(r, ["Padpath", "PadPath"], default=None)
        chanda_raw = _get_first_existing(r, ["Chanda"], default=None)

        feats = extract_features_for_mantra(
            mantra_id=mantra_id,
            source_veda="samaveda",
            text_dev=text_dev,
            padapatha=padpath,
            chanda_raw=chanda_raw,
            transliteration=None,
            veda_profile="sama_kauthuma",
            domain="saman",
        )
        feat_dict = mantra_features_to_dict(feats)

        parsed_list = parse_chanda_cell(chanda_raw or "")
        if parsed_list:
            parsed = parsed_list[0]
            try:
                first_pada_syllables = int(
                    str(feat_dict["syllable_count_per_pada"]).split(",")[0]
                )
            except Exception:
                first_pada_syllables = None
            parsed = compute_deviation_D(parsed, first_pada_syllables)
            feat_dict["meter_gold_base"] = parsed.base_meter
            feat_dict["meter_variant_prefixes"] = " ".join(parsed.variant_prefixes)
            feat_dict["meter_deviation"] = parsed.deviation_label
            feat_dict["deviation_vector"] = (
                "" if parsed.deviation_D is None else str(parsed.deviation_D)
            )

        # Stobha detection for Sāma (very approximate)
        text = text_dev
        if any(s in text for s in ["हो", "हि", "है", "हौ", "ओ"]):
            feat_dict["has_stobha"] = True

        rows.append(feat_dict)

    out_df = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    out_df.to_csv(output_csv, index=False)
    print(f"Enriched dataset written to {output_csv}")


if __name__ == "__main__":
    # Default paths for your renamed CSVs:
    rig = os.path.join(DATA_DIR, "raw", "only_Rigveda.csv")
    yaj = os.path.join(DATA_DIR, "raw", "only_Yajurveda.csv")
    sama = os.path.join(DATA_DIR, "raw", "only_Samveda.csv")
    out = os.path.join(DATA_DIR, "processed", "dataset_enriched.csv")
    build_enriched_dataset(rig, yaj, sama, out)
