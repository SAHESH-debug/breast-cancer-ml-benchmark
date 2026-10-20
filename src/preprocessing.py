"""
preprocessing.py
-----------------
Builds leak-proof sklearn Pipelines and the stratified train/test split.

WHY A PIPELINE (not scaling X up front, like a simpler script might):
If you fit a StandardScaler on the WHOLE dataset before splitting or
cross-validating, information from the validation/test folds leaks into
the scaling parameters (mean/std) used to transform the training folds.
That's data leakage -- it makes CV scores look slightly better than the
model would actually achieve on genuinely new data.

Wrapping scaler + model in a single sklearn Pipeline, then calling
cross_val_score / GridSearchCV on the *pipeline*, ensures the scaler is
re-fit on only the training fold every single time -- the test fold (or
held-out test set) is only ever .transform()'d, never .fit()'d on.
"""

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

RANDOM_STATE = 42
TEST_SIZE = 0.2


def split_data(X, y):
    """Stratified train/test split.

    Stratification matters here because the classes are imbalanced
    (roughly 63/37 in WDBC). A plain random split could, by chance,
    put too few malignant cases in the test set, making the evaluation
    unreliable. Stratifying forces both the train and test sets to keep
    the same class ratio as the full dataset.
    """
    return train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )


def build_pipeline(estimator, needs_scaling: bool, has_missing: bool = False) -> Pipeline:
    """Builds a Pipeline: [impute?] -> [scale?] -> classifier.

    Only models that are actually distance/gradient-sensitive (Logistic
    Regression, KNN, SVM) get a scaler -- tree-based models (Decision
    Tree, Random Forest) are scale-invariant by construction, so scaling
    them adds pipeline overhead with no benefit, which is also a useful
    point to be able to explain in a viva.
    """
    steps = []
    if has_missing:
        steps.append(("imputer", SimpleImputer(strategy="median")))
    if needs_scaling:
        steps.append(("scaler", StandardScaler()))
    steps.append(("clf", estimator))
    return Pipeline(steps)
