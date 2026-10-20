"""
evaluation.py
-------------
Computes the full metric set required by the brief: accuracy, precision,
recall, specificity, F1, ROC-AUC, PR-AUC, and the confusion matrix -- all
derived correctly from true/predicted labels and predicted probabilities.

Convention used throughout this project: the POSITIVE class for precision/
recall/specificity is MALIGNANT (target=0 in sklearn's WDBC encoding),
because in a screening context the clinically important question is
"did we catch the malignant cases" -- not benign cases.
"""

from __future__ import annotations
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve
)

POSITIVE_CLASS = 0  # malignant, in sklearn's WDBC target encoding


def compute_metrics(y_true, y_pred, y_proba_positive) -> dict:
    """
    y_proba_positive: predicted probability of the POSITIVE class (malignant).
    """
    cm = confusion_matrix(y_true, y_pred, labels=[POSITIVE_CLASS, 1 - POSITIVE_CLASS])
    tp, fn = cm[0]
    fp, tn = cm[1]

    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, pos_label=POSITIVE_CLASS, zero_division=0),
        "recall": recall_score(y_true, y_pred, pos_label=POSITIVE_CLASS, zero_division=0),
        "specificity": specificity,
        "f1": f1_score(y_true, y_pred, pos_label=POSITIVE_CLASS, zero_division=0),
        "roc_auc": roc_auc_score(1 - np.array(y_true), y_proba_positive),  # flip so malignant=1 for AUC math
        "pr_auc": average_precision_score(1 - np.array(y_true), y_proba_positive),
        "confusion_matrix": cm.tolist(),  # [[TP, FN], [FP, TN]]
        "tp": int(tp), "fn": int(fn), "fp": int(fp), "tn": int(tn),
    }


def get_roc_curve(y_true, y_proba_positive):
    fpr, tpr, thresholds = roc_curve(1 - np.array(y_true), y_proba_positive)
    return fpr.tolist(), tpr.tolist(), thresholds.tolist()


def metric_definitions() -> dict:
    """Plain-language + formula definitions, used by the dashboard and README."""
    return {
        "Accuracy": "Overall % of predictions that were correct. (TP+TN)/(TP+TN+FP+FN)",
        "Precision": "Of everything predicted as the adverse class, how much really was. TP/(TP+FP)",
        "Recall (Sensitivity)": "Of everything that really was the adverse class, how much was caught. TP/(TP+FN)",
        "Specificity": "Of everything that really was the other class, how much was correctly cleared. TN/(TN+FP)",
        "F1-Score": "Harmonic mean of Precision and Recall. 2*(P*R)/(P+R)",
        "ROC-AUC": "Chance the model ranks a random adverse case above a random other case, across every possible threshold. 0.5 = guessing, 1.0 = perfect.",
        "PR-AUC": "Like ROC-AUC but focused on the adverse class -- more informative when classes are imbalanced.",
    }
