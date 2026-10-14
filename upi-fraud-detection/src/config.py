"""Shared paths and column definitions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "upi_fraud_dataset.csv"
MODELS_DIR = ROOT / "models"
FIG_DIR = ROOT / "reports" / "figures"
REPORTS_DIR = ROOT / "reports"

TARGET = "fraud_risk"

# upi_number is a unique row ID (2,666 unique values in 2,666 rows), zip is
# noise, and trans_year is constant (2022) -- none carry predictive signal,
# so they are excluded from modelling.
FEATURES = ["trans_hour", "trans_day", "trans_month",
            "category", "age", "trans_amount", "state"]
CATEGORICAL = ["category", "state"]          # coded labels, not magnitudes
NUMERIC = [f for f in FEATURES if f not in CATEGORICAL]

RANDOM_STATE = 42
TEST_SIZE = 0.20

# Risk bands used in the app and plots (probability of fraud)
RISK_BANDS = [(0.0, 0.30, "Low"), (0.30, 0.70, "Medium"), (0.70, 1.01, "High")]


def risk_level(p: float) -> str:
    for lo, hi, name in RISK_BANDS:
        if lo <= p < hi:
            return name
    return "High"
