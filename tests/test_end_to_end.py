"""
tests/test_end_to_end.py

End-to-end smoke test of:

- build_enriched_dataset (on a small subset)
- train_baseline_model (on that subset)
- analyze_verse (no crash, reasonable outputs)

This does NOT assert strong metric performance; it only checks that the
pipeline runs end-to-end without exceptions and shape mismatches.
"""

from __future__ import annotations

import os
import pandas as pd

from src.build_dataset import build_enriched_dataset, DATA_DIR
from src.train_baseline_model import train_baseline
from src.analyze_text import analyze_verse


def _subset_csv(in_path: str, out_path: str, n: int = 20) -> None:
    df = pd.read_csv(in_path)
    df.head(n).to_csv(out_path, index=False)


def test_end_to_end(tmp_path):
    # Prepare small subsets in a temp dir
    raw_dir = os.path.join(DATA_DIR, "raw")
    rig_full = os.path.join(raw_dir, "only_Rigveda.csv")
    yaj_full = os.path.join(raw_dir, "only_Yajurveda.csv")
    sam_full = os.path.join(raw_dir, "only_Samveda.csv")

    rig_small = tmp_path / "rig_small.csv"
    yaj_small = tmp_path / "yaj_small.csv"
    sam_small = tmp_path / "sam_small.csv"

    _subset_csv(rig_full, rig_small, n=20)
    _subset_csv(yaj_full, yaj_small, n=20)
    _subset_csv(sam_full, sam_small, n=20)

    out_enriched = tmp_path / "dataset_enriched_small.csv"
    build_enriched_dataset(str(rig_small), str(yaj_small), str(sam_small), str(out_enriched))

    # Train a tiny model
    model_out = tmp_path / "baseline_meter_clf.joblib"
    _, df_test = train_baseline(str(out_enriched), str(model_out), report_out=None)

    # Ensure we have at least one prediction
    assert not df_test.empty
    assert "meter_pred" in df_test.columns

    # Run analyze_verse on RV 1.1.1 text (from your Rigveda CSV)
    rig_df = pd.read_csv(rig_full)
    rv_111 = rig_df[
        (rig_df["Mandal"] == 1) & (rig_df["Sukta"] == 1) & (rig_df["Mantra Number"] == 1)
    ]["MantraText"].iloc[0]

    # Just check that analyze_verse runs without error
    analyze_verse(rv_111)
