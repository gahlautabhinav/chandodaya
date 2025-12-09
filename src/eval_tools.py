"""
eval_tools.py

Evaluation and debugging utilities for the meter classifier.

Features
--------
- Confusion matrix plotting (text-based)
- Top-k error inspection: which true meters get confused with which
- Simple CLI entry-points for error analysis
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from tabulate import tabulate
from sklearn.metrics import confusion_matrix


def print_confusion_matrix(y_true: Iterable[str], y_pred: Iterable[str]) -> None:
    """
    Print confusion matrix as ASCII table.
    """
    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    df = pd.DataFrame(cm, index=labels, columns=labels)
    print("Confusion matrix (rows=true, cols=pred):")
    print(tabulate(df, headers="keys", tablefmt="psql"))


def top_confusions(
    df_test: pd.DataFrame, top_k: int = 10
) -> Iterable[Tuple[str, str, int]]:
    """
    Compute most frequent (true, pred) error pairs.
    """
    errors = df_test[df_test["meter_pred"] != df_test["meter_gold_base"]]
    pairs = list(zip(errors["meter_gold_base"], errors["meter_pred"]))
    cnt = Counter(pairs)
    return cnt.most_common(top_k)


def print_top_confusions(df_test: pd.DataFrame, top_k: int = 10) -> None:
    print("Top confusions:")
    for (true_m, pred_m), c in top_confusions(df_test, top_k=top_k):
        print(f"{true_m:15s} → {pred_m:15s}  {c}")


if __name__ == "__main__":
    # mini-demo with fake data
    y_true = ["gayatri", "trishtubh", "gayatri", "jagati", "trishtubh"]
    y_pred = ["gayatri", "gayatri", "trishtubh", "jagati", "trishtubh"]
    print_confusion_matrix(y_true, y_pred)
