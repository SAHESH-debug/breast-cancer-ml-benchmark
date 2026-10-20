"""
explainability.py
------------------
Feature importance, permutation importance, and SHAP for the best model.

SIMPLE-LANGUAGE SUMMARY (used verbatim in the dashboard/report):
"SHAP shows how each feature pushes an individual prediction toward
benign or malignant." -- it doesn't just say "this feature matters
overall" (that's what feature importance / permutation importance do);
it explains ONE specific prediction at a time: for this one patient,
how much did their 'worst concave points' value push the model's
output toward malignant, versus toward benign.

No medical claims are made from these numbers -- they describe what the
MODEL learned to rely on, not an established clinical ranking of risk
factors.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance


def tree_feature_importance(fitted_pipeline, feature_names, save_path, top_n=12):
    """Only valid for tree-based models (Decision Tree, Random Forest)."""
    clf = fitted_pipeline.named_steps["clf"]
    if not hasattr(clf, "feature_importances_"):
        return None
    importances = pd.Series(clf.feature_importances_, index=feature_names)
    importances = importances.sort_values(ascending=False).head(top_n)
    plt.figure(figsize=(9, 7))
    importances[::-1].plot(kind="barh", color="#3498db")
    plt.title("Feature Importance (built into the model)")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()
    return importances.to_dict()


def compute_permutation_importance(fitted_pipeline, X_test, y_test, save_path, top_n=12):
    """
    Model-agnostic: works for ANY model (even SVM/KNN with no built-in
    importance). Shuffles one feature's values at a time and measures
    how much accuracy drops -- a bigger drop means the model relied on
    that feature more.
    """
    result = permutation_importance(
        fitted_pipeline, X_test, y_test, n_repeats=10, random_state=42, scoring="accuracy"
    )
    importances = pd.Series(result.importances_mean, index=X_test.columns)
    importances = importances.sort_values(ascending=False).head(top_n)
    plt.figure(figsize=(9, 7))
    importances[::-1].plot(kind="barh", color="#e67e22")
    plt.title("Permutation Importance (model-agnostic)")
    plt.xlabel("Mean Accuracy Drop When Feature Is Shuffled")
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()
    return importances.to_dict()


def compute_shap_summary(fitted_pipeline, X_background, X_explain, save_path, max_display=12):
    """
    SHAP summary plot for the final model. Uses a small background sample
    for computational practicality (per brief section 10: "if
    computationally practical").
    """
    import shap

    clf = fitted_pipeline.named_steps["clf"]
    # transform X through every step except the final classifier
    X_bg_t = X_background.copy()
    X_ex_t = X_explain.copy()
    for name, step in fitted_pipeline.steps[:-1]:
        X_bg_t = step.transform(X_bg_t)
        X_ex_t = step.transform(X_ex_t)

    # Use a small background sample to keep this computationally light
    bg_sample = shap.sample(X_bg_t, min(50, len(X_bg_t)), random_state=42)

    try:
        explainer = shap.Explainer(clf.predict_proba, bg_sample)
        shap_values = explainer(X_ex_t[: min(100, len(X_ex_t))])
        # class index 1 or 0 depending on clf.classes_ ordering
        pos_idx = list(clf.classes_).index(0)  # malignant
        plt.figure()
        shap.summary_plot(
            shap_values[..., pos_idx], X_ex_t[: min(100, len(X_ex_t))],
            feature_names=X_explain.columns, show=False, max_display=max_display
        )
        plt.title("SHAP Summary — Impact on Adverse-Class Prediction")
        plt.tight_layout()
        plt.savefig(save_path, dpi=140, bbox_inches="tight")
        plt.close()
        return True
    except Exception as e:
        print(f"SHAP computation skipped (non-fatal): {e}")
        return False
