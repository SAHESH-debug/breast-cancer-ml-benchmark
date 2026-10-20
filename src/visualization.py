"""
visualization.py
-----------------
Every chart here answers a specific question (per brief section 9) rather
than being generated for its own sake:
  - class_distribution      -> "Are the classes balanced?"
  - correlation_heatmap      -> "Which features move together?"
  - feature_distributions    -> "Do malignant/benign separate on this feature?"
  - pca_scatter               -> "Can the classes be separated in 2D?"
  - pca_explained_variance    -> "How much information do fewer dimensions keep?"
  - roc_curves_comparison     -> "How do the 5 models compare across thresholds?"
  - confusion_matrix_heatmap  -> "What kind of mistakes does this model make?"
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

sns.set_style("whitegrid")


def class_distribution(y, target_names, save_path):
    counts = y.value_counts().sort_index()
    labels = [target_names[i] for i in counts.index]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    colors = ["#e74c3c", "#2ecc71"]
    axes[0].bar(labels, counts.values, color=colors)
    axes[0].set_title("Class Distribution (Count)")
    for i, v in enumerate(counts.values):
        axes[0].text(i, v + 3, str(v), ha="center", fontweight="bold")
    axes[1].pie(counts.values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
    axes[1].set_title("Class Distribution (%)")
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()


def correlation_heatmap(X, save_path, max_features=15):
    # limit to top-variance features for readability if there are many
    cols = X.var().sort_values(ascending=False).index[:max_features]
    corr = X[cols].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, cmap="coolwarm", center=0, annot=False, square=True, linewidths=0.4)
    plt.title("Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()


def feature_distributions(X, y, target_names, save_path, top_n=6):
    corr_with_target = X.apply(lambda col: abs(col.corr(y)))
    top_feats = corr_with_target.sort_values(ascending=False).index[:top_n]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.ravel()
    labels = y.map(target_names)
    for i, feat in enumerate(top_feats):
        sns.kdeplot(x=X[feat], hue=labels, fill=True, ax=axes[i], alpha=0.5,
                    palette={target_names[0]: "#e0527f", target_names[1]: "#12a7a0"})
        axes[i].set_title(feat, fontsize=10)
    plt.suptitle("Top Features Most Correlated With Diagnosis", y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()


def pca_analysis(X, y, target_names, scatter_path, variance_path):
    """Answers: 'can the classes be separated in reduced dimensions?'"""
    X_scaled = StandardScaler().fit_transform(X.fillna(X.median()))  # EDA only: median-fill so PCA can run
    pca_full = PCA().fit(X_scaled)
    cum_var = np.cumsum(pca_full.explained_variance_ratio_)

    # explained variance plot
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(cum_var) + 1), cum_var, marker="o", markersize=3)
    plt.axhline(0.95, color="red", linestyle="--", linewidth=1, label="95% variance")
    plt.xlabel("Number of Principal Components")
    plt.ylabel("Cumulative Explained Variance")
    plt.title("PCA: How Much Information Do Fewer Dimensions Keep?")
    plt.legend()
    plt.tight_layout()
    plt.savefig(variance_path, dpi=140, bbox_inches="tight")
    plt.close()

    # 2D scatter of first 2 PCs
    pca2 = PCA(n_components=2).fit_transform(X_scaled)
    labels = y.map(target_names)
    plt.figure(figsize=(7, 6))
    sns.scatterplot(x=pca2[:, 0], y=pca2[:, 1], hue=labels,
                     palette={target_names[0]: "#e0527f", target_names[1]: "#12a7a0"}, alpha=0.7, s=40)
    plt.xlabel(f"PC1 ({pca_full.explained_variance_ratio_[0]*100:.1f}% variance)")
    plt.ylabel(f"PC2 ({pca_full.explained_variance_ratio_[1]*100:.1f}% variance)")
    plt.title("PCA: Class Separation in 2 Dimensions")
    plt.tight_layout()
    plt.savefig(scatter_path, dpi=140, bbox_inches="tight")
    plt.close()

    return {
        "n_components_for_95pct_variance": int(np.argmax(cum_var >= 0.95) + 1),
        "pc1_variance_pct": float(pca_full.explained_variance_ratio_[0] * 100),
        "pc2_variance_pct": float(pca_full.explained_variance_ratio_[1] * 100),
    }


def roc_curves_comparison(results: dict, save_path):
    """results: {model_name: {'roc_fpr':.., 'roc_tpr':.., 'roc_auc':..}}"""
    plt.figure(figsize=(8, 7))
    for model_name, r in results.items():
        plt.plot(r["roc_fpr"], r["roc_tpr"], linewidth=2,
                  label=f"{model_name} (AUC={r['roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random classifier (AUC=0.5)")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves — All 5 Models")
    plt.legend(loc="lower right", fontsize=9)
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()


def confusion_matrix_heatmap(cm, model_name, save_path):
    """cm is [[TP, FN], [FP, TN]] as produced by evaluation.compute_metrics"""
    import numpy as np
    arr = np.array(cm)
    plt.figure(figsize=(5.5, 5))
    sns.heatmap(arr, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Pred positive", "Pred negative"],
                yticklabels=["Actual positive", "Actual negative"],
                annot_kws={"size": 15, "fontweight": "bold"})
    plt.title(f"Confusion Matrix — {model_name}")
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()


def model_comparison_bars(df, save_path):
    """df: the results dataframe for ONE dataset (rows = 5 models)"""
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(df))
    width = 0.15
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"]
    for i, m in enumerate(metrics):
        ax.bar(x + i * width, df[m], width, label=m, color=colors[i])
    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(df["model"], rotation=20, ha="right")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right", ncol=5, fontsize=8)
    ax.set_title("Model Comparison — All Metrics")
    plt.tight_layout()
    plt.savefig(save_path, dpi=140, bbox_inches="tight")
    plt.close()
