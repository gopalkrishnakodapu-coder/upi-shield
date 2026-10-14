"""Data loading and splitting."""
import pandas as pd
from sklearn.model_selection import train_test_split

from .config import DATA_PATH, FEATURES, TARGET, RANDOM_STATE, TEST_SIZE


def load_data() -> pd.DataFrame:
    """Load the raw UPI transaction dataset (first column is a saved index)."""
    return pd.read_csv(DATA_PATH, index_col=0)


def split_data(df: pd.DataFrame):
    """Stratified train/test split on the modelling features."""
    X, y = df[FEATURES], df[TARGET]
    return train_test_split(X, y, test_size=TEST_SIZE,
                            stratify=y, random_state=RANDOM_STATE)
