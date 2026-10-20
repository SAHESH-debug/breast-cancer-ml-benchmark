"""
data_loader.py
---------------
Loads the 5 breast-cancer datasets used in this project.

Convention used everywhere: target y == 0 is the ADVERSE / POSITIVE class
(malignant, recurrence, died within 5 years, event), y == 1 is the other
class. So "recall" always means "how many of the adverse cases were caught".

Raw files are bundled in data/raw/ so the project runs offline. WDBC comes
from scikit-learn's bundled copy.

Datasets (all genuinely different problems):
  wdbc       Wisconsin Diagnostic      569 x 30  diagnosis  (UCI, cell-nucleus measurements)
  wbcd       Wisconsin Original        699 x  9  diagnosis  (UCI, cytology scores 1-10)
  ljubljana  Ljubljana Recurrence      286 x  9  prognosis  (UCI, recurrence after surgery)
  haberman   Haberman Survival         306 x  3  prognosis  (UCI, 5-year survival after surgery)
  gbsg2      German Breast Cancer 2    686 x  8  prognosis  (GBSG trial, via scikit-survival)
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from sklearn.datasets import load_breast_cancer

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def _pack(short, name, X, y, target_names, task, source, desc, feature_types, note=""):
    X = X.reset_index(drop=True)
    y = pd.Series(y).reset_index(drop=True).astype(int).rename("target")
    return {
        "name": name, "short_name": short, "X": X, "y": y,
        "target_names": target_names, "task": task, "source": source,
        "description": desc, "feature_types": feature_types, "note": note,
        "n_samples": X.shape[0], "n_features": X.shape[1],
        "missing_values": int(X.isnull().sum().sum()),
        "duplicates": int(pd.concat([X, y], axis=1).duplicated().sum()),
    }


def load_wdbc() -> dict:
    d = load_breast_cancer()
    X = pd.DataFrame(d.data, columns=d.feature_names)
    return _pack(
        "wdbc", "WDBC - Wisconsin Diagnostic", X, d.target,
        {0: "Malignant", 1: "Benign"}, "Diagnosis",
        "UCI ML Repository, dataset 17 (Street, Wolberg & Mangasarian, 1993)",
        "Measurements of cell nuclei from fine-needle-aspirate images: 10 properties, each as mean / error / worst.",
        "30 numeric")


def load_wbcd() -> dict:
    df = pd.read_csv(RAW_DIR / "wbcd.csv").drop(columns=["Id"])
    X = df.drop(columns=["Class"])
    X.columns = ["clump_thickness", "cell_size_uniformity", "cell_shape_uniformity",
                 "marginal_adhesion", "epithelial_cell_size", "bare_nuclei",
                 "bland_chromatin", "normal_nucleoli", "mitoses"]
    y = df["Class"].map({1: 0, 0: 1})  # file: 1=malignant, 0=benign -> malignant = 0
    return _pack(
        "wbcd", "WBCD - Wisconsin Original", X, y,
        {0: "Malignant", 1: "Benign"}, "Diagnosis",
        "UCI ML Repository, dataset 15 (Wolberg & Mangasarian, 1990); R package mlbench copy",
        "Nine cytology scores (1-10) assigned by a pathologist to each sample.",
        "9 ordinal (1-10)", "Missing values in bare_nuclei are imputed (median) inside the pipeline.")


def load_ljubljana() -> dict:
    df = pd.read_csv(RAW_DIR / "ljubljana.csv", keep_default_na=False)
    y = df["class"].map({"recurrence-events": 0, "no-recurrence-events": 1})
    X = df.drop(columns=["class"]).copy()
    # ordered ranges -> ordinal numbers (position in sorted range order)
    def ordinal(col):
        order = sorted(X[col].unique(), key=lambda s: int(s.split("-")[0]))
        return X[col].map({v: i for i, v in enumerate(order)})
    for c in ["age", "tumor_size", "inv_nodes"]:
        X[c] = ordinal(c)
    X["menopause"] = X["menopause"].map({"lt40": 0, "ge40": 1, "premeno": 0.5})
    X = pd.get_dummies(X, columns=["node_caps", "breast", "breast_quad", "irradiat"], dtype=float)
    return _pack(
        "ljubljana", "Ljubljana - Recurrence", X, y,
        {0: "Recurrence", 1: "No recurrence"}, "Prognosis",
        "UCI ML Repository, dataset 14 (Institute of Oncology, Ljubljana)",
        "Clinical details (age, tumor size, nodes, grade, irradiation...) to predict cancer recurrence.",
        "9 categorical -> encoded",
        "Categorical ranges converted to ordered numbers; other categories one-hot encoded. Missing categories kept as their own 'unknown' value.")


def load_haberman() -> dict:
    df = pd.read_csv(RAW_DIR / "haberman.csv")
    y = df["status"].map({2: 0, 1: 1})  # 2 = died within 5 years
    X = df.drop(columns=["status"])
    return _pack(
        "haberman", "Haberman - 5-Year Survival", X, y,
        {0: "Died within 5 yrs", 1: "Survived 5+ yrs"}, "Prognosis",
        "UCI ML Repository, dataset 43 (University of Chicago Billings Hospital)",
        "Age, year of operation and number of positive axillary nodes to predict 5-year survival.",
        "3 numeric", "Contains some repeated rows (kept, as they are different patients with identical values).")


def load_gbsg2() -> dict:
    df = pd.read_csv(RAW_DIR / "gbsg2.csv")
    y = df["cens"].map({1: 0, 0: 1})  # 1 = recurrence or death event
    X = df.drop(columns=["cens", "time"]).copy()  # follow-up time NOT used as a feature (outcome leak)
    X["horTh"] = (X["horTh"] == "yes").astype(float)
    X["menostat"] = (X["menostat"] == "Post").astype(float)
    X["tgrade"] = X["tgrade"].map({"I": 1, "II": 2, "III": 3}).astype(float)
    return _pack(
        "gbsg2", "GBSG2 - German Breast Cancer", X, y,
        {0: "Event (recurrence/death)", 1: "Event-free"}, "Prognosis",
        "German Breast Cancer Study Group 2 trial (Schumacher et al., 1994); loaded via scikit-survival",
        "Clinical and receptor data (age, grade, nodes, hormone therapy...) to predict a recurrence/death event.",
        "8 numeric/binary",
        "Follow-up time differs between patients, so the label is a simplification of survival data. Follow-up time is excluded from features.")


REGISTRY = {"wdbc": load_wdbc, "wbcd": load_wbcd, "ljubljana": load_ljubljana,
            "haberman": load_haberman, "gbsg2": load_gbsg2}


def available_datasets() -> list[str]:
    return list(REGISTRY.keys())


def load_dataset(short_name: str) -> dict:
    if short_name not in REGISTRY:
        raise ValueError(f"Unknown dataset '{short_name}'. Available: {available_datasets()}")
    return REGISTRY[short_name]()


if __name__ == "__main__":
    for k in REGISTRY:
        d = load_dataset(k)
        print(f"{d['name']:<34} {d['n_samples']:>4} x {d['n_features']:<3} "
              f"missing={d['missing_values']:<3} dup={d['duplicates']:<3} {d['y'].value_counts().sort_index().to_dict()}")
