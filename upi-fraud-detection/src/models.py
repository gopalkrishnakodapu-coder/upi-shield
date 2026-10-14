"""Model definitions. Both models are sklearn Pipelines so preprocessing
travels with the model when it is saved and loaded."""
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import CATEGORICAL, NUMERIC, RANDOM_STATE


def build_random_forest() -> Pipeline:
    # Trees do not need scaling or one-hot encoding.
    return Pipeline([
        ("model", RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2,
            random_state=RANDOM_STATE, n_jobs=-1)),
    ])


def build_logistic_regression() -> Pipeline:
    # Linear model: scale numeric columns, one-hot the coded categorical ones.
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    return Pipeline([
        ("pre", pre),
        ("model", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
    ])
