"""
model_utils.py

Shared helpers for loading trained meter-classifier models and
preparing feature DataFrames for inference.

This centralizes the mapping from `MantraFeatures` to the ML model's
expected input columns.
"""

from __future__ import annotations

import os
from typing import Optional

import joblib
import pandas as pd

from .feature_extractor import MantraFeatures, mantra_features_to_dict

# models/ directory relative to src/
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

BASELINE_MODEL_NAME = "baseline_meter_clf.joblib"
MLP_MODEL_NAME = "mlp_meter_clf.joblib"
FULLCHANDA_MODEL_NAME = "baseline_fullchanda_clf.joblib"  # NEW


def load_model(name: str = BASELINE_MODEL_NAME):
    """
    Load a trained model from the models/ directory.

    Parameters
    ----------
    name : str
        Filename inside `models` folder.

    Returns
    -------
    model or None
        Loaded scikit-learn Pipeline, or None if file not found.
    """
    path = os.path.join(MODEL_DIR, name)
    if not os.path.exists(path):
        return None
    return joblib.load(path)


def features_to_model_input(
    feat: MantraFeatures, override_source_veda: Optional[str] = None
) -> pd.DataFrame:
    """
    Convert a MantraFeatures instance to a single-row DataFrame
    compatible with the training pipelines (baseline + MLP + full-chanda).

    Parameters
    ----------
    feat : MantraFeatures
        Features produced by extract_features_for_mantra.
    override_source_veda : Optional[str]
        If provided, replaces `feat.source_veda` in the model input.
        Useful when running on arbitrary classical verses where you
        want to label them as "unknown" or a guessed veda.

    Returns
    -------
    pd.DataFrame
        Columns: L_G_sequence, source_veda, has_pluti, has_stobha
    """
    d = mantra_features_to_dict(feat)
    source_veda = override_source_veda or d["source_veda"]

    data = {
        "L_G_sequence": [d["L_G_sequence"]],
        "source_veda": [source_veda],
        "has_pluti": [bool(d["has_pluti"])],
        "has_stobha": [bool(d["has_stobha"])],
    }
    return pd.DataFrame(data)
