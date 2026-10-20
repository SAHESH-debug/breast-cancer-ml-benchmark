"""
models.py
---------
Defines the 5 classification algorithms used in this project, each paired
with a small, reasonable hyperparameter search grid for GridSearchCV.

WHY THESE 5 (and not more):
The brief asks not to "blindly include every algorithm." These 5 cover
the major families of classifier so the comparison is meaningful rather
than redundant:
  - Logistic Regression -> linear, parametric, highly interpretable
  - KNN                 -> instance-based, non-parametric, no training phase
  - Decision Tree        -> rule-based, non-linear, interpretable but
                             prone to overfitting alone
  - Random Forest        -> ensemble (bagging) of many trees
  - SVM (RBF)             -> margin-based, kernel method, non-linear

XGBoost/AdaBoost/MLP were deliberately left out to keep the search space
and runtime reasonable for a normal laptop, per the brief's own instruction
not to create an unnecessarily enormous search space.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

RANDOM_STATE = 42

# Each entry: (estimator, hyperparameter grid for GridSearchCV)
# Grids are kept small deliberately -- this is about demonstrating correct
# methodology, not an exhaustive search.
MODEL_REGISTRY = {
    "Logistic Regression": {
        "estimator": LogisticRegression(max_iter=5000, random_state=RANDOM_STATE),
        "param_grid": {
            "clf__C": [0.01, 0.1, 1, 10],
        },
        "needs_scaling": True,
        "why": (
            "Linear baseline. Learns one weight per feature; fast, highly "
            "interpretable (coefficients show each feature's direction and "
            "strength of influence), and a strong fit when classes are "
            "close to linearly separable -- worth testing first."
        ),
    },
    "K-Nearest Neighbors": {
        "estimator": KNeighborsClassifier(),
        "param_grid": {
            "clf__n_neighbors": [3, 5, 7, 9, 11],
        },
        "needs_scaling": True,
        "why": (
            "Non-parametric baseline with zero assumptions about the "
            "decision boundary's shape -- classifies purely by similarity "
            "to nearby labeled points. Most sensitive of the 5 to feature "
            "scaling, which makes it a useful check that scaling was done "
            "correctly."
        ),
    },
    "Decision Tree": {
        "estimator": DecisionTreeClassifier(random_state=RANDOM_STATE),
        "param_grid": {
            "clf__max_depth": [3, 5, 7, None],
            "clf__min_samples_leaf": [1, 3, 5],
        },
        "needs_scaling": False,
        "why": (
            "Simple, fully interpretable rule-based model (a flowchart of "
            "feature thresholds). Included partly as a baseline that "
            "Random Forest (many trees) can be compared against directly, "
            "to demonstrate why ensembling trees tends to help."
        ),
    },
    "Random Forest": {
        "estimator": RandomForestClassifier(random_state=RANDOM_STATE),
        "param_grid": {
            "clf__n_estimators": [100, 200],
            "clf__max_depth": [None, 10],
            "clf__min_samples_leaf": [1, 2],
        },
        "needs_scaling": False,
        "why": (
            "Ensemble of many decision trees (bagging) -- each tree sees a "
            "random bootstrap sample and a random feature subset, and "
            "predictions are combined by majority vote. Usually more "
            "robust than a single tree, and gives real feature-importance "
            "scores for free."
        ),
    },
    "SVM (RBF Kernel)": {
        "estimator": SVC(probability=True, random_state=RANDOM_STATE),
        "param_grid": {
            "clf__C": [0.1, 1, 10],
            "clf__gamma": ["scale", "auto"],
        },
        "needs_scaling": True,
        "why": (
            "Margin-based method: finds the boundary that maximizes the "
            "gap between the two classes' closest points. The RBF kernel "
            "lets that boundary curve, so it can separate classes that "
            "aren't simply linearly separable -- a useful non-linear "
            "counterpoint to Logistic Regression."
        ),
    },
}


def get_model_names() -> list[str]:
    return list(MODEL_REGISTRY.keys())
