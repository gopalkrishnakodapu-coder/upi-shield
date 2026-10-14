"""Load trained models and score a single new transaction."""
import joblib
import pandas as pd

from .config import FEATURES, MODELS_DIR, risk_level

MODEL_FILES = {
    "Random Forest": MODELS_DIR / "random_forest.joblib",
    "Logistic Regression": MODELS_DIR / "logistic_regression.joblib",
}


def load_models() -> dict:
    return {name: joblib.load(path) for name, path in MODEL_FILES.items()}


def predict_transaction(models: dict, transaction: dict) -> dict:
    """transaction: dict with keys in config.FEATURES.
    Returns {model_name: {"probability": float, "prediction": int, "risk": str}}."""
    row = pd.DataFrame([transaction])[FEATURES]
    out = {}
    for name, model in models.items():
        p = float(model.predict_proba(row)[0, 1])
        out[name] = {"probability": p, "prediction": int(p >= 0.5),
                     "risk": risk_level(p)}
    return out


if __name__ == "__main__":
    sample = {"trans_hour": 2, "trans_day": 14, "trans_month": 6, "category": 4,
              "age": 35, "trans_amount": 850.0, "state": 22}
    for model, res in predict_transaction(load_models(), sample).items():
        print(f"{model:20s} P(fraud)={res['probability']:.2f}  risk={res['risk']}")
