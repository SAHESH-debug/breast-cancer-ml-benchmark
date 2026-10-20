"""
training.py
------------
Orchestrates, for a given dataset: stratified split -> for each of the 5
models -> GridSearchCV (with internal StratifiedKFold) on the TRAIN set
only -> refit best params on full train set -> evaluate ONCE on the
untouched test set -> save the fitted pipeline + metrics.

This is the single place where "fair comparison" (brief section 4) and
"hyperparameter tuning" (section 5) actually happen.
"""

from __future__ import annotations
import time
import json
import joblib
from pathlib import Path
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score

from src.models import MODEL_REGISTRY
from src.preprocessing import build_pipeline, split_data
from src.evaluation import compute_metrics, get_roc_curve

CV_FOLDS = 5
RANDOM_STATE = 42

MODELS_DIR = Path(__file__).resolve().parent.parent / "models" / "trained_models"
EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent / "experiments"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)


def run_experiment_for_dataset(dataset: dict) -> dict:
    """
    dataset: the dict returned by src.data_loader.load_dataset(...)
    Returns: dict of {model_name: result_dict}, and also writes files to disk.
    """
    X, y = dataset["X"], dataset["y"]
    has_missing = dataset["missing_values"] > 0
    X_train, X_test, y_train, y_test = split_data(X, y)

    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    results = {}

    for model_name, cfg in MODEL_REGISTRY.items():
        pipe = build_pipeline(cfg["estimator"], cfg["needs_scaling"], has_missing)

        # --- Hyperparameter tuning (train set only, internal CV) ---
        t0 = time.time()
        grid = GridSearchCV(
            pipe, cfg["param_grid"], cv=skf, scoring="accuracy", n_jobs=-1
        )
        grid.fit(X_train, y_train)
        train_time = time.time() - t0

        best_pipe = grid.best_estimator_

        # --- 5-fold CV accuracy of the BEST config, for reporting stability ---
        cv_scores = cross_val_score(best_pipe, X_train, y_train, cv=skf, scoring="accuracy")

        # --- Evaluate ONCE on the untouched test set ---
        t0 = time.time()
        y_pred = best_pipe.predict(X_test)
        y_proba = best_pipe.predict_proba(X_test)[:, list(best_pipe.classes_).index(0)]  # P(malignant)
        predict_time = time.time() - t0

        metrics = compute_metrics(y_test, y_pred, y_proba)
        fpr, tpr, _ = get_roc_curve(y_test, y_proba)

        # --- Save fitted pipeline ---
        model_filename = f"{dataset['short_name']}__{model_name.replace(' ', '_').replace('(', '').replace(')', '')}.pkl"
        joblib.dump(best_pipe, MODELS_DIR / model_filename)

        results[model_name] = {
            "dataset": dataset["short_name"],
            "model": model_name,
            "best_params": grid.best_params_,
            "cv_mean_accuracy": float(cv_scores.mean()),
            "cv_std_accuracy": float(cv_scores.std()),
            **metrics,
            "roc_fpr": fpr,
            "roc_tpr": tpr,
            "train_time_sec": round(train_time, 4),
            "predict_time_sec": round(predict_time, 4),
            "n_features": X.shape[1],
            "model_file": model_filename,
        }
        print(f"  [{dataset['short_name']}] {model_name:<22} "
              f"acc={metrics['accuracy']:.4f}  recall={metrics['recall']:.4f}  "
              f"f1={metrics['f1']:.4f}  auc={metrics['roc_auc']:.4f}  "
              f"(best params: {grid.best_params_})")

    return results


def save_results_csv(all_results: dict, path: Path):
    """all_results: {dataset_short_name: {model_name: result_dict}}"""
    import pandas as pd
    rows = []
    for ds_name, model_results in all_results.items():
        for model_name, r in model_results.items():
            rows.append({
                "dataset": r["dataset"],
                "model": r["model"],
                "accuracy": r["accuracy"],
                "precision": r["precision"],
                "recall": r["recall"],
                "specificity": r["specificity"],
                "f1": r["f1"],
                "roc_auc": r["roc_auc"],
                "pr_auc": r["pr_auc"],
                "cv_mean_accuracy": r["cv_mean_accuracy"],
                "cv_std_accuracy": r["cv_std_accuracy"],
                "tp": r["tp"], "fn": r["fn"], "fp": r["fp"], "tn": r["tn"],
                "train_time_sec": r["train_time_sec"],
                "predict_time_sec": r["predict_time_sec"],
                "n_features": r["n_features"],
                "best_params": json.dumps(r["best_params"]),
            })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return df
