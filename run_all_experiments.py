"""
run_all_experiments.py
------------------------
Top-level script. Runs the full pipeline for every available dataset:
load -> EDA plots -> PCA -> train+tune all 5 models with CV -> evaluate
on held-out test set -> explainability -> save everything to disk.

Run this once with:  python3 run_all_experiments.py
The dashboard/app.py then just READS the saved results -- it never
retrains on startup (per brief section 18).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.data_loader import load_dataset, available_datasets
from src.training import run_experiment_for_dataset, save_results_csv
from src.preprocessing import split_data
from src import visualization as viz
from src import explainability as expl

EXPERIMENTS_DIR = ROOT / "experiments"
PLOTS_DIR = ROOT / "experiments" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    all_results = {}

    for ds_name in available_datasets():
        print(f"\n{'='*70}\nDATASET: {ds_name}\n{'='*70}")
        dataset = load_dataset(ds_name)
        X, y = dataset["X"], dataset["y"]
        tn = dataset["target_names"]
        ds_plot_dir = PLOTS_DIR / ds_name
        ds_plot_dir.mkdir(parents=True, exist_ok=True)

        # ---- EDA ----
        print("Generating EDA plots...")
        viz.class_distribution(y, tn, ds_plot_dir / "class_distribution.png")
        viz.correlation_heatmap(X, ds_plot_dir / "correlation_heatmap.png")
        viz.feature_distributions(X, y, tn, ds_plot_dir / "feature_distributions.png")

        # ---- PCA ----
        print("Running PCA...")
        pca_stats = viz.pca_analysis(
            X, y, tn,
            ds_plot_dir / "pca_scatter.png",
            ds_plot_dir / "pca_explained_variance.png",
        )
        print(f"  PCA: {pca_stats['n_components_for_95pct_variance']} components "
              f"needed for 95% variance; PC1={pca_stats['pc1_variance_pct']:.1f}%, "
              f"PC2={pca_stats['pc2_variance_pct']:.1f}%")

        # ---- Train + tune all 5 models ----
        print("Training & tuning 5 models (this is the slow part)...")
        results = run_experiment_for_dataset(dataset)
        all_results[ds_name] = results

        # ---- Model comparison plots ----
        import pandas as pd
        df_ds = pd.DataFrame([
            {"model": m, **{k: r[k] for k in
                             ["accuracy", "precision", "recall", "f1", "roc_auc"]}}
            for m, r in results.items()
        ])
        viz.model_comparison_bars(df_ds, ds_plot_dir / "model_comparison.png")
        viz.roc_curves_comparison(results, ds_plot_dir / "roc_curves.png")

        best_model_name = df_ds.loc[df_ds["accuracy"].idxmax(), "model"]
        viz.confusion_matrix_heatmap(
            results[best_model_name]["confusion_matrix"], best_model_name,
            ds_plot_dir / "confusion_matrix_best_model.png"
        )
        print(f"  Best model on {ds_name}: {best_model_name} "
              f"(accuracy={results[best_model_name]['accuracy']:.4f})")

        # ---- Explainability (on best model) ----
        print("Computing explainability (permutation importance + SHAP)...")
        import joblib
        from src.training import MODELS_DIR
        best_pipe = joblib.load(MODELS_DIR / results[best_model_name]["model_file"])
        X_train, X_test, y_train, y_test = split_data(X, y)

        tree_imp = expl.tree_feature_importance(
            best_pipe, X.columns, ds_plot_dir / "feature_importance.png"
        )
        perm_imp = expl.compute_permutation_importance(
            best_pipe, X_test, y_test, ds_plot_dir / "permutation_importance.png"
        )
        shap_ok = expl.compute_shap_summary(
            best_pipe, X_train, X_test, ds_plot_dir / "shap_summary.png"
        )
        print(f"  Tree importance available: {tree_imp is not None} | "
              f"Permutation importance: done | SHAP: {'done' if shap_ok else 'skipped'}")

        # Save explainability results alongside the dataset's results
        with open(ds_plot_dir / "explainability.json", "w") as f:
            json.dump({
                "best_model": best_model_name,
                "tree_feature_importance": tree_imp,
                "permutation_importance": perm_imp,
                "shap_computed": shap_ok,
            }, f, indent=2)

    # ---- Save master results CSV ----
    df = save_results_csv(all_results, EXPERIMENTS_DIR / "results.csv")
    print(f"\n\nSaved {len(df)} total experiment rows to experiments/results.csv")

    # ---- Save a JSON version too (dashboard consumes this) ----
    with open(EXPERIMENTS_DIR / "results_full.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print("\nALL EXPERIMENTS COMPLETE.")
    print(df[["dataset", "model", "accuracy", "recall", "f1", "roc_auc"]].to_string(index=False))


if __name__ == "__main__":
    main()
