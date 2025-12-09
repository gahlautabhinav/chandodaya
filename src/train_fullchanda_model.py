"""
train_fullchanda_model.py

Train a classifier to predict a *rich* chanda label that includes:

- base meter family (gayatri, trishtubh, jagati, etc.)
- variant prefixes (brahmi, yajushi, archi, etc.)
- deviation labels (nichrid, bhurik, viraj, svaraj)

We build a canonical "full chanda label" per row, for example:

- "gayatri"
- "brahmi trishtubh"
- "svaraj brihati"
- "nichrid gayatri"
- etc.

If meter_gold_base is missing but meter_gold_raw exists, we fall back
to a normalized version of the raw label so that we cover additional
chandas beyond the 7 Pingala families.

Usage (from project root)
-------------------------
python -m src.train_fullchanda_model

Requirements
------------
- data/processed/dataset_enriched.csv must exist
  (created by: python -m src.build_dataset)

Outputs
-------
- models/baseline_fullchanda_clf.joblib
- classification report printed to stdout
"""

from __future__ import annotations

import os
from typing import Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Directories relative to src/
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

FULLCHANDA_MODEL_FILENAME = "baseline_fullchanda_clf.joblib"


def _build_full_chanda_label(row: pd.Series) -> str | None:
    """
    Build a canonical "full chanda label" string for a given row.

    Priority:
    ---------
    1. If meter_gold_base is present, combine:
       [meter_deviation] + meter_variant_prefixes + meter_gold_base
       e.g. "svaraj brahmi trishtubh"

    2. Else if meter_gold_raw is present, return that normalized
       (strip whitespace).

    3. Else return None (row will be dropped).
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
        label = " ".join(parts)
        return label

    # Fallback: use raw label if available
    if isinstance(raw, str) and raw.strip():
        return raw.strip()

    return None


def load_dataset(path: str) -> pd.DataFrame:
    """
    Load the enriched dataset CSV.
    """
    return pd.read_csv(path)


def build_pipeline() -> Pipeline:
    """
    Build a ColumnTransformer + LogisticRegression pipeline.

    Features
    --------
    - char n-grams of L_G_sequence (2-5)
    - one-hot of source_veda, has_pluti, has_stobha

    (Same feature space as the baseline meter family classifier.)
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

    clf = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",  # mitigate class imbalance
    )

    pipe = Pipeline(
        steps=[
            ("pre", preprocessor),
            ("clf", clf),
        ]
    )
    return pipe


def train_fullchanda(
    dataset_path: str,
    model_out: str,
    min_examples_per_class: int = 2,
) -> Tuple[Pipeline, pd.DataFrame]:
    """
    Train the "full chanda" model and persist it.

    Parameters
    ----------
    dataset_path : str
        Path to data/processed/dataset_enriched.csv
    model_out : str
        Output path for the joblib model
    min_examples_per_class : int, default 2
        Minimum number of examples per class to keep. Classes with fewer
        examples are dropped before training to avoid stratified split
        errors and degenerate classes.

    Returns
    -------
    (Pipeline, pd.DataFrame)
        Trained pipeline and a test-set DataFrame with predictions.
    """
    df = load_dataset(dataset_path)

    # Construct full chanda label
    df["meter_full_label"] = df.apply(_build_full_chanda_label, axis=1)
    df = df.dropna(subset=["meter_full_label"])

    if df.empty:
        raise ValueError("No usable chanda labels found in dataset_enriched.csv")

    # Filter out ultra-rare labels (with < min_examples_per_class occurrences)
    vc = df["meter_full_label"].value_counts()
    keep_labels = vc[vc >= min_examples_per_class].index
    df = df[df["meter_full_label"].isin(keep_labels)]

    print(f"Total rows after filtering rare labels: {len(df)}")
    print(f"Number of distinct chhanda labels: {df['meter_full_label'].nunique()}")

    if df.empty:
        raise ValueError(
            f"No classes have at least {min_examples_per_class} examples. "
            f"Try lowering min_examples_per_class."
        )

    X = df[["L_G_sequence", "source_veda", "has_pluti", "has_stobha"]]
    y = df["meter_full_label"].astype(str)

    unique_classes = set(y)
    if len(unique_classes) < 2:
        raise ValueError(f"Need at least 2 classes to train, got {len(unique_classes)}")

    # stratify only if it is feasible
    stratify = y if len(unique_classes) > 1 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipe, model_out)

    y_pred = pipe.predict(X_test)
    print("=== Full-chanda classification report ===")
    print(classification_report(y_test, y_pred))

    test_df = X_test.copy()
    test_df["meter_full_label"] = y_test
    test_df["meter_pred"] = y_pred
    return pipe, test_df


if __name__ == "__main__":
    dataset_path = os.path.join(DATA_DIR, "processed", "dataset_enriched.csv")
    model_out = os.path.join(MODEL_DIR, FULLCHANDA_MODEL_FILENAME)
    train_fullchanda(dataset_path, model_out)
