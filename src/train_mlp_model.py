"""
train_mlp_model.py

Train a slightly "deeper" meter classifier using scikit-learn's
MLPClassifier on top of the same feature representation as the
baseline model.

This satisfies the "baseline + deep" requirement without adding
heavy dependencies like TensorFlow or PyTorch.

Usage (from project root)
-------------------------
python -m src.train_mlp_model

Requirements
------------
- data/processed/dataset_enriched.csv must exist
  (created by: python -m src.build_dataset)

Outputs
-------
- models/mlp_meter_clf.joblib
- classification report printed to stdout
"""

from __future__ import annotations

import os
from typing import Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Directories relative to src/
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


def load_dataset(path: str) -> pd.DataFrame:
    """
    Load the enriched dataset CSV.

    Parameters
    ----------
    path : str
        Path to dataset_enriched.csv

    Returns
    -------
    pd.DataFrame
    """
    return pd.read_csv(path)


def build_mlp_pipeline() -> Pipeline:
    """
    Build a ColumnTransformer + MLP pipeline.

    Features
    --------
    - char n-grams of L_G_sequence (2-5)
    - one-hot of source_veda, has_pluti, has_stobha
    """
    cat_features = ["source_veda", "has_pluti", "has_stobha"]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "lg_ngrams",
                CountVectorizer(analyzer="char", ngram_range=(2, 5)),
                "L_G_sequence",
            ),
            (
                "cats",
                OneHotEncoder(handle_unknown="ignore"),
                cat_features,
            ),
        ]
    )

    clf = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation="relu",
        solver="adam",
        max_iter=50,  # start small; you can increase later
        random_state=42,
    )

    pipe = Pipeline(
        steps=[
            ("pre", preprocessor),
            ("clf", clf),
        ]
    )
    return pipe


def train_mlp(
    dataset_path: str,
    model_out: str,
) -> Tuple[Pipeline, pd.DataFrame]:
    """
    Train the MLP-based model and persist it.

    Parameters
    ----------
    dataset_path : str
        Path to data/processed/dataset_enriched.csv
    model_out : str
        Output path for the joblib model

    Returns
    -------
    (Pipeline, pd.DataFrame)
        Trained pipeline and a test-set DataFrame with predictions.
    """
    df = load_dataset(dataset_path)
    # Keep only rows with a known meter label
    df = df.dropna(subset=["meter_gold_base"])

    if df.empty:
        raise ValueError("No rows with meter_gold_base found in dataset_enriched.csv")

    X = df[["L_G_sequence", "source_veda", "has_pluti", "has_stobha"]]
    y = df["meter_gold_base"].astype(str)

    # stratify only if there is more than one class
    stratify = y if len(set(y)) > 1 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    pipe = build_mlp_pipeline()
    pipe.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipe, model_out)

    y_pred = pipe.predict(X_test)
    print("=== MLP classification report ===")
    print(classification_report(y_test, y_pred))

    test_df = X_test.copy()
    test_df["meter_gold_base"] = y_test
    test_df["meter_pred"] = y_pred
    return pipe, test_df


if __name__ == "__main__":
    dataset_path = os.path.join(DATA_DIR, "processed", "dataset_enriched.csv")
    model_out = os.path.join(MODEL_DIR, "mlp_meter_clf.joblib")
    train_mlp(dataset_path, model_out)
