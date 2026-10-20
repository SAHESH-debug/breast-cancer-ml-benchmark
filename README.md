# Breast Cancer Prediction Using Machine Learning

A complete, reproducible machine-learning project that compares **five classification algorithms** on
**five public breast-cancer datasets**, then lets you explore every result in an interactive **Streamlit dashboard**.

> **Educational prototype. Not a medical diagnostic tool.** Predictions are statistical estimates and must never replace a doctor's judgment.

**Team:** Aravindhan (CB.SC.U4AIE25159), Sathyanarayanan (CB.SC.U4AIE25155), Sahesh (CB.SC.U4AIE25149), Nihara (CB.SC.U4AIE25139)
B.Tech CSE (AI), Amrita Vishwa Vidyapeetham

---

## 1. What this project does

Given patient data, the models predict a binary outcome. Two kinds of problem are covered:

- **Diagnosis**: is a tumor malignant or benign? (WDBC, WBCD)
- **Prognosis**: what happens after treatment, such as cancer recurrence or survival? (Ljubljana, Haberman, GBSG2)

The same workflow is applied identically to every dataset, so the comparison is fair. The main finding:
diagnosis datasets are classified well, prognosis datasets are much harder, and the best algorithm changes from dataset to dataset.

**Label convention:** label `0` is always the *adverse* class (malignant, recurrence, died within 5 years, or event) and `1` is the other class.
So **recall** always means "how many adverse cases did we catch", which is the metric that matters most in medicine.

## 2. Datasets

All raw files are bundled in `data/raw/`, so the project runs offline. WDBC loads from scikit-learn, and GBSG2 is also bundled as a CSV.

| Dataset | Task | Samples | Features | Source |
|---|---|---|---|---|
| WDBC - Wisconsin Diagnostic | Diagnosis | 569 | 30 | UCI ML Repository (Street, Wolberg & Mangasarian, 1993) |
| WBCD - Wisconsin Original | Diagnosis | 699 | 9 | UCI ML Repository (Wolberg & Mangasarian, 1990) |
| Ljubljana - Recurrence | Prognosis | 286 | 18 (after encoding) | UCI ML Repository (Institute of Oncology, Ljubljana) |
| Haberman - 5-Year Survival | Prognosis | 306 | 3 | UCI ML Repository (University of Chicago Billings Hospital) |
| GBSG2 - German Breast Cancer | Prognosis | 686 | 8 | German Breast Cancer Study Group 2 trial (Schumacher et al., 1994) |

Known quirks (handled and documented in `src/data_loader.py` and in the dashboard): WBCD has a few missing values and many repeated rows,
Ljubljana and GBSG2 contain categories that are encoded to numbers, and GBSG2 follow-up time is excluded because it would leak the label.

## 3. Method

1. **Split first.** Stratified 80/20 train/test split (`random_state=42`) before anything else, so the test set is never seen during training.
2. **Leak-proof pipeline.** Median imputer, then `StandardScaler` (only for Logistic Regression, KNN and SVM), then the classifier, all inside one scikit-learn `Pipeline`, so preprocessing is fitted on training data only.
3. **Tuning.** `GridSearchCV` with stratified 5-fold cross-validation on the training set only, using a small grid per model.
4. **One final test.** The chosen model is evaluated once on the held-out test set.
5. **Metrics.** Accuracy, precision, recall, F1, ROC-AUC and the confusion matrix. Recall on the adverse class is the one to watch.
6. **Explainability.** Permutation importance and SHAP, to show which features drive predictions.

**Algorithms** (five families, so the comparison is meaningful): Logistic Regression (linear), K-Nearest Neighbors (distance-based),
Decision Tree (rule-based), Random Forest (ensemble) and SVM with RBF kernel (margin-based).

## 4. Project structure

```
bc_full_project/
├── app.py                    # Streamlit dashboard (reads saved results only, never retrains)
├── run_all_experiments.py    # Runs the full pipeline for all 5 datasets and saves results
├── requirements.txt          # Pinned dependencies
├── .streamlit/config.toml    # Dashboard theme
├── src/
│   ├── data_loader.py        # Loads and cleans the 5 datasets (REGISTRY)
│   ├── preprocessing.py      # Stratified split and pipeline construction
│   ├── models.py             # The 5 algorithms and their tuning grids
│   ├── training.py           # GridSearchCV training and test evaluation
│   ├── evaluation.py         # Metrics and confusion matrix helpers
│   ├── explainability.py     # Permutation importance and SHAP
│   └── visualization.py      # EDA, PCA and result plots
├── data/raw/                 # Bundled raw dataset files
├── experiments/              # Generated: results.csv, results_full.json, plots/
├── models/trained_models/    # Generated: one saved pipeline per dataset and model
└── report/                   # project_report.md and viva_questions.md
```

## 5. How to run

**Requirements:** Python 3.10 or newer (tested on 3.10 to 3.13).

```bash
# 1. Go into the project folder
cd bc_full_project

# 2. (Recommended) create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Train, tune and evaluate everything (a few minutes; saves to experiments/ and models/)
python run_all_experiments.py

# 5. Launch the dashboard (opens at http://localhost:8501)
streamlit run app.py
```

If `experiments/` and `models/trained_models/` are already present in the project, you can skip step 4 and go straight to the dashboard.

> **Important:** start the dashboard with `streamlit run app.py`, **not** `python app.py`.
> Running it with plain `python` shows "missing ScriptRunContext" warnings and does not open a page.

Other handy commands:

```bash
streamlit run app.py --server.port 8502     # use a different port if 8501 is busy
python run_all_experiments.py               # re-run to regenerate every result and plot
```

## 6. Dashboard pages

| Page | What it shows |
|---|---|
| Overview | Project summary and the best model per dataset |
| Dataset Explorer | Pick any of the five datasets: size, class balance, data quirks and a preview |
| Data Insights | Class counts, feature relationships and PCA for the chosen dataset |
| Model Comparison | All five algorithms side by side on the held-out test set |
| Model Details | Confusion matrix, ROC curve, tuned settings and feature importance for one model |
| Predict | Enter values (or load a real test patient), choose a model, get a class and a probability |
| About | Method, limitations and references |

Each page has short captions explaining what you are looking at.

## 7. Results (held-out test set)
| dataset   | model               |   accuracy |   recall |    f1 |   roc_auc |
|:----------|:--------------------|-----------:|---------:|------:|----------:|
| wdbc      | Logistic Regression |      0.974 |    0.952 | 0.964 |     0.996 |
| wdbc      | K-Nearest Neighbors |      0.974 |    0.929 | 0.963 |     0.994 |
| wdbc      | Decision Tree       |      0.939 |    0.905 | 0.916 |     0.944 |
| wdbc      | Random Forest       |      0.956 |    0.929 | 0.94  |     0.994 |
| wdbc      | SVM (RBF Kernel)    |      0.982 |    0.976 | 0.976 |     0.995 |
| wbcd      | Logistic Regression |      0.95  |    0.917 | 0.926 |     0.991 |
| wbcd      | K-Nearest Neighbors |      0.936 |    0.917 | 0.907 |     0.973 |
| wbcd      | Decision Tree       |      0.936 |    0.938 | 0.909 |     0.959 |
| wbcd      | Random Forest       |      0.95  |    0.938 | 0.928 |     0.987 |
| wbcd      | SVM (RBF Kernel)    |      0.943 |    0.938 | 0.918 |     0.98  |
| ljubljana | Logistic Regression |      0.741 |    0.294 | 0.4   |     0.755 |
| ljubljana | K-Nearest Neighbors |      0.81  |    0.353 | 0.522 |     0.694 |
| ljubljana | Decision Tree       |      0.724 |    0.588 | 0.556 |     0.724 |
| ljubljana | Random Forest       |      0.672 |    0.235 | 0.296 |     0.646 |
| ljubljana | SVM (RBF Kernel)    |      0.741 |    0.235 | 0.348 |     0.678 |
| haberman  | Logistic Regression |      0.742 |    0.062 | 0.111 |     0.777 |
| haberman  | K-Nearest Neighbors |      0.71  |    0.188 | 0.25  |     0.571 |
| haberman  | Decision Tree       |      0.694 |    0.25  | 0.296 |     0.52  |
| haberman  | Random Forest       |      0.726 |    0.25  | 0.32  |     0.624 |
| haberman  | SVM (RBF Kernel)    |      0.71  |    0.125 | 0.182 |     0.55  |
| gbsg2     | Logistic Regression |      0.652 |    0.367 | 0.478 |     0.689 |
| gbsg2     | K-Nearest Neighbors |      0.63  |    0.533 | 0.557 |     0.624 |
| gbsg2     | Decision Tree       |      0.601 |    0.533 | 0.538 |     0.631 |
| gbsg2     | Random Forest       |      0.594 |    0.45  | 0.491 |     0.648 |
| gbsg2     | SVM (RBF Kernel)    |      0.594 |    0.367 | 0.44  |     0.667 |


## 8. Honest limitations
- Small datasets; no external validation; one random split (small differences between top models are noise).
- WBCD contains many repeated rows, which can appear in both train and test and inflate scores.
- Prognosis datasets (Ljubljana, Haberman, GBSG2) are much harder than diagnosis datasets; recall for the adverse class is low.
- GBSG2's label is a simplification of survival data (follow-up time differs between patients and is not used).
- Not clinically validated and not tested on other populations, including Indian patients. Do not use for real medical decisions.

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| "missing ScriptRunContext" warnings | You ran `python app.py`. Use `streamlit run app.py`. |
| Dashboard says results are missing | Run `python run_all_experiments.py` first. |
| `ModuleNotFoundError` | Activate your virtual environment and run `pip install -r requirements.txt`. |
| Port already in use | Add `--server.port 8502` to the streamlit command. |
| SHAP install fails | Try `pip install shap` on its own (it needs a recent Python and numpy), then re-run `python run_all_experiments.py`. |

## 10. References

- Street WN, Wolberg WH, Mangasarian OL. Nuclear feature extraction for breast tumor diagnosis. Proc. SPIE 1905, 1993.
- UCI Machine Learning Repository: Breast Cancer Wisconsin (Diagnostic and Original), Breast Cancer (Ljubljana), Haberman's Survival.
- Schumacher M, et al. Randomized 2x2 trial evaluating hormonal treatment and the duration of chemotherapy in node-positive breast cancer patients. J Clin Oncol. 1994;12(10):2086-2093.
- Pedregosa F, et al. Scikit-learn: Machine learning in Python. JMLR 12:2825-2830, 2011.
- Lundberg SM, Lee SI. A unified approach to interpreting model predictions. NeurIPS, 2017.
