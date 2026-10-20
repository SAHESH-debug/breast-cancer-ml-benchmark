# Project Report: Breast Cancer Classification Using Machine Learning

## 1. Abstract
This project builds and compares 5 machine learning classifiers on the
Wisconsin Diagnostic Breast Cancer (WDBC) dataset, predicting malignant vs.
benign tumor diagnosis from 30 numeric biopsy-derived features. SVM (RBF
kernel) achieved the best test-set accuracy (98.25%), narrowly ahead of
Logistic Regression (97.37%, highest ROC-AUC at 0.9957). All results were
obtained with stratified cross-validation, leak-proof preprocessing
pipelines, and GridSearchCV hyperparameter tuning.

## 2. Introduction
Manual biopsy diagnosis depends on pathologist experience. This project
investigates whether quantitative cell-nucleus measurements alone are
sufficient for a classifier to learn a reliable malignant/benign
distinction, and which classical algorithm fits this specific data best.

## 3. Problem Statement
Binary classification: given 30 numeric features per patient, predict
malignant (0) or benign (1).

## 4. Objectives
See README section 3.

## 5. Background
The WDBC dataset originates from Street, Wolberg & Mangasarian's 1993 work
on nuclear feature extraction from fine-needle-aspirate biopsy images,
using active-contour ("snake") boundary tracing. It is one of the most
widely benchmarked datasets in applied ML literature, making this
project's results directly comparable to a large body of published work.

## 6. Dataset Description
See README section 5. 569 samples, 30 features, 212 malignant / 357
benign, zero missing values.

## 7. Data Preprocessing
- Stratified 80/20 train/test split (`random_state=42`)
- `StandardScaler` for scale-sensitive models (Logistic Regression, KNN,
  SVM), applied inside an sklearn `Pipeline` to avoid data leakage
- No scaling applied for tree-based models (Decision Tree, Random Forest),
  which are scale-invariant by construction
- No missing-value imputation needed for WDBC (zero missing values
  confirmed programmatically)

## 8. Exploratory Data Analysis
Four questions were asked of the data before modeling:
1. **Are the classes balanced?** Mildly imbalanced (63%/37%) — tracked via
   precision/recall/F1, not accuracy alone.
2. **Which features move together?** Radius, perimeter, and area correlate
   strongly (all describe tumor size).
3. **Do malignant/benign separate on individual features?** Yes, visibly,
   for features like `worst concave points`.
4. **Can the classes be separated in reduced dimensions?** Yes — visible
   separation even in just the first 2 principal components (PC1 explains
   44.3% of variance alone).

## 9. Algorithms
See README section 6 for the 5 algorithms and rationale for each.

## 10. Experimental Methodology
`StratifiedKFold(n_splits=5)` cross-validation inside `GridSearchCV`,
fit only on the training split. The best configuration per model is then
evaluated exactly once on the untouched test set. This two-stage process
(tune via CV on train, evaluate once on test) prevents the test metrics
from being inflated by indirectly "peeking" at the test set during tuning.

## 11. Hyperparameter Tuning
| Model | Parameters tuned | Why |
|---|---|---|
| Logistic Regression | `C` (regularization strength) | Controls overfitting vs. underfitting of the linear boundary |
| KNN | `n_neighbors` | Controls local vs. broad decision regions |
| Decision Tree | `max_depth`, `min_samples_leaf` | Controls overfitting of a single tree |
| Random Forest | `n_estimators`, `max_depth`, `min_samples_leaf` | Ensemble size and individual tree complexity |
| SVM | `C`, `gamma` | Margin softness and RBF kernel reach |

Best parameters and CV scores for each are in `experiments/results.csv`
(`best_params`, `cv_mean_accuracy`, `cv_std_accuracy` columns) — not
reproduced as illustrative numbers here, since the brief requires observed
results only.

## 12. Evaluation Metrics
See README section 8 for formulas and definitions.

## 13. Results
See README section 12 for the full observed comparison table.

## 14. Model Comparison
SVM (RBF) and Logistic Regression are statistically close (98.25% vs.
97.37% accuracy, both >0.995 ROC-AUC) — both near-linear and near-maximal
margin solutions converge to similar decision boundaries on this dataset,
suggesting the two classes are close to linearly separable in the original
feature space. Decision Tree, un-ensembled, is the clear weakest performer
(93.86%), motivating Random Forest's inclusion as a bagged alternative.

## 15. Feature Analysis
Permutation importance and SHAP (computed on the best model, SVM) overlap
but rank features differently. Permutation importance's top five were
`worst area`, `radius error`, `worst smoothness`, `worst radius` and
`worst texture`; SHAP's top five were `worst texture`, `worst concave
points`, `worst radius`, `worst smoothness` and `worst area`. Both point to
the "worst" (most severe) measurements carrying the most signal, consistent
with the EDA findings. Neither is a clinical risk ranking.

## 16. Explainability
SHAP values describe, per prediction, how far each feature's value pushed
that specific prediction toward malignant or benign (not a global ranking
of clinical risk factors). Permutation importance is model-agnostic and
was used specifically because SVM has no built-in feature importance.

## 17. UI Design
Two interfaces were built: (1) a full Streamlit app (`app.py`, 8 pages,
runs locally) and (2) a standalone interactive HTML dashboard (built from
the same saved results, viewable with no installation). Both cover:
Dashboard/Overview, Dataset Explorer, EDA, Model Comparison, Confusion
Matrix, ROC Curve, Feature Importance, and Prediction.

## 18. Limitations
See README section 13.

## 19. Ethical Considerations
See README section 15. No individual-level patient data beyond the public
WDBC dataset was used; all data is anonymized and sourced from a published
academic dataset under CC BY 4.0.

## 20. Future Scope
See README section 14.

## 21. Conclusion
A correctly-validated, leak-proof comparison of 5 classical ML algorithms
on WDBC shows SVM (RBF) and Logistic Regression both achieve >97% test
accuracy and >0.995 ROC-AUC, with the data's near-linear separability
being the likely explanation for why simpler models compete so closely
with more complex ones here. The project's honest scope limitation — one
dataset rather than the originally intended multi-dataset comparison — is
documented transparently rather than concealed.

## 22. References
1. Street, W.N., Wolberg, W.H., Mangasarian, O.L. (1993). Nuclear Feature
   Extraction for Breast Tumor Diagnosis. *Proc. SPIE 1905*, 861–870.
2. UCI Machine Learning Repository: Breast Cancer Wisconsin (Diagnostic)
   Data Set. archive.ics.uci.edu/dataset/17
3. Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python.
   *JMLR* 12, 2825-2830.
4. Lundberg, S.M., Lee, S.I. (2017). A Unified Approach to Interpreting
   Model Predictions. *NeurIPS*.
