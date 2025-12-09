"""
train_baseline_model.py

Train a baseline meter classifier on the enriched dataset.

Model
-----
We start with a simple scikit-learn baseline:

- Features:
    * character n-grams of L/G sequences
    * per-pada syllable counts
    * simple booleans like has_pluti, has_stobha, source_veda

- Label:
    * `meter_gold_base` (e.g. gayatri, trishtubh, jagati, ...)

You can swap in more advanced models later (e.g. BiLSTM over syllable
sequences, transformers over Devanagari).
"""

from __future__ import annotations

import os
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


def load_dataset(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def build_pipeline() -> Pipeline:
    """
    Build a ColumnTransformer + classifier pipeline.

    Textual feature: L_G_sequence
    Numeric feature: syllable_count_per_pada (encoded as string, but we can
                    vectorize as n-gram too)
    Categorical features: source_veda, has_pluti, has_stobha
    """
    text_features = ["L_G_sequence"]
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

    from sklearn.linear_model import LogisticRegression

    clf = LogisticRegression(max_iter=1000, multi_class="auto")

    pipe = Pipeline(
        steps=[
            ("pre", preprocessor),
            ("clf", clf),
        ]
    )
    return pipe


def train_baseline(
    dataset_path: str,
    model_out: str,
    report_out: str | None = None,
) -> Tuple[Pipeline, pd.DataFrame]:
    """
    Train the baseline model and persist it.

    Returns trained pipeline and the test-set DataFrame (with predictions).
    """
    df = load_dataset(dataset_path)
    df = df.dropna(subset=["meter_gold_base"])
    X = df[["L_G_sequence", "source_veda", "has_pluti", "has_stobha"]]
    y = df["meter_gold_base"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipe, model_out)

    y_pred = pipe.predict(X_test)
    print(classification_report(y_test, y_pred))

    if report_out:
        with open(report_out, "w", encoding="utf-8") as f:
            f.write(classification_report(y_test, y_pred))

    # attach predictions into a copy of test df
    test_df = X_test.copy()
    test_df["meter_gold_base"] = y_test
    test_df["meter_pred"] = y_pred
    return pipe, test_df


if __name__ == "__main__":
    dataset_path = os.path.join(DATA_DIR, "processed", "dataset_enriched.csv")
    model_out = os.path.join(MODEL_DIR, "baseline_meter_clf.joblib")
    report_out = os.path.join(MODEL_DIR, "baseline_report.txt")
    train_baseline(dataset_path, model_out, report_out)
