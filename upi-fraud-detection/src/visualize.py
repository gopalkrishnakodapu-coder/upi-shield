"""All plotting functions. Each returns a matplotlib Figure so the same code
feeds both the saved report images and the Streamlit app."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import ConfusionMatrixDisplay, roc_curve

from .config import TARGET

sns.set_theme(style="whitegrid", context="notebook")
PALETTE = {0: "#2E86AB", 1: "#D1495B"}   # blue = legit, red = fraud
LABELS = {0: "Legitimate", 1: "Fraud risk"}
AMOUNT_BINS = [0, 50, 200, 500, 1000, np.inf]
AMOUNT_LABELS = ["<=50", "50-200", "200-500", "500-1000", ">1000"]


# ------------------------------------------------------------------ analysis
def plot_class_balance(df: pd.DataFrame):
    counts = df[TARGET].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar([LABELS[i] for i in counts.index], counts.values,
                  color=[PALETTE[i] for i in counts.index])
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v}\n({v / counts.sum():.1%})",
                ha="center", va="bottom")
    ax.set_ylabel("Transactions"); ax.set_title("Class balance")
    ax.set_ylim(0, counts.max() * 1.18)
    fig.tight_layout(); return fig


def plot_amount_distribution(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(data=df.assign(label=df[TARGET].map(LABELS)), x="trans_amount",
                 hue="label", log_scale=True, bins=40, element="step",
                 palette={LABELS[k]: v for k, v in PALETTE.items()}, ax=ax)
    ax.set_xlabel("Transaction amount (log scale)")
    ax.set_title("Transaction amount by class")
    fig.tight_layout(); return fig


def _rate_bar(df, by, title, xlabel, rotate=0):
    rate = df.groupby(by, observed=True)[TARGET].mean()
    overall = df[TARGET].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(rate.index.astype(str), rate.values, color="#D1495B", alpha=.85)
    ax.axhline(overall, color="black", ls="--", lw=1,
               label=f"Overall rate {overall:.0%}")
    ax.set_ylim(0, 1); ax.set_ylabel("Fraud rate")
    ax.set_xlabel(xlabel); ax.set_title(title); ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=rotate)
    fig.tight_layout(); return fig


def plot_fraud_by_amount_band(df: pd.DataFrame):
    bands = pd.cut(df["trans_amount"], AMOUNT_BINS, labels=AMOUNT_LABELS)
    return _rate_bar(df.assign(band=bands), "band",
                     "Fraud rate by transaction amount", "Amount band")


def plot_fraud_by_hour(df: pd.DataFrame):
    return _rate_bar(df, "trans_hour", "Fraud rate by hour of day", "Hour (0-23)")


def plot_fraud_by_category(df: pd.DataFrame):
    return _rate_bar(df, "category", "Fraud rate by merchant category code",
                     "Category code")


def plot_fraud_by_age_group(df: pd.DataFrame):
    groups = pd.cut(df["age"], [0, 25, 35, 45, 60, 120],
                    labels=["<=25", "26-35", "36-45", "46-60", "60+"])
    return _rate_bar(df.assign(grp=groups), "grp",
                     "Fraud rate by age group", "Age group")


def plot_hour_amount_heatmap(df: pd.DataFrame):
    """Fraud rate across hour-block x amount-band."""
    d = df.assign(
        hour_block=pd.cut(df["trans_hour"], [-1, 5, 11, 17, 23],
                          labels=["00-05", "06-11", "12-17", "18-23"]),
        amount_band=pd.cut(df["trans_amount"], AMOUNT_BINS, labels=AMOUNT_LABELS))
    pivot = d.pivot_table(index="hour_block", columns="amount_band",
                          values=TARGET, aggfunc="mean", observed=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.heatmap(pivot, annot=True, fmt=".0%", cmap="Reds", vmin=0, vmax=1, ax=ax)
    ax.set_title("Fraud rate: time of day x amount")
    ax.set_xlabel("Amount band"); ax.set_ylabel("Hour block")
    fig.tight_layout(); return fig


def plot_correlation(df: pd.DataFrame, features):
    corr = df[list(features) + [TARGET]].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Feature correlation")
    fig.tight_layout(); return fig


# --------------------------------------------------------------------- models
def plot_confusion_matrices(results: dict):
    """results: {name: (y_true, y_pred)}"""
    fig, axes = plt.subplots(1, len(results), figsize=(5.2 * len(results), 4.5))
    axes = np.atleast_1d(axes)
    for ax, (name, (yt, yp)) in zip(axes, results.items()):
        ConfusionMatrixDisplay.from_predictions(
            yt, yp, display_labels=["Legit", "Fraud"], cmap="Blues",
            colorbar=False, ax=ax)
        ax.set_title(name); ax.grid(False)
    fig.suptitle("Confusion matrices (test set)", y=1.02)
    fig.tight_layout(); return fig


def plot_metric_comparison(metrics: pd.DataFrame):
    cols = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    m = metrics[cols].reset_index().melt("model", var_name="metric")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(data=m, x="metric", y="value", hue="model",
                palette=["#2E86AB", "#D1495B"], ax=ax)
    for c in ax.containers:
        ax.bar_label(c, fmt="%.2f", fontsize=8, padding=2)
    ax.set_ylim(0, 1.1); ax.set_ylabel("Score"); ax.set_xlabel("")
    ax.set_title("Model comparison (test set)")
    fig.tight_layout(); return fig


def plot_roc_curves(curves: dict):
    """curves: {name: (y_true, y_score)}"""
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for name, (yt, ys) in curves.items():
        fpr, tpr, _ = roc_curve(yt, ys)
        ax.plot(fpr, tpr, lw=2, label=name)
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.set_title("ROC curves"); ax.legend(loc="lower right")
    fig.tight_layout(); return fig


def plot_feature_importance(names, impurity, permutation):
    order = np.argsort(impurity)
    names = np.array(names)[order]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    axes[0].barh(names, np.array(impurity)[order], color="#2E86AB")
    axes[0].set_title("Random Forest impurity importance")
    axes[1].barh(names, np.array(permutation)[order], color="#D1495B")
    axes[1].set_title("Permutation importance (test set)")
    axes[0].set_xlabel("Importance"); axes[1].set_xlabel("Drop in F1 when shuffled")
    fig.tight_layout(); return fig


def plot_risk_score_distribution(y_true, proba):
    fig, ax = plt.subplots(figsize=(7, 4))
    y_true, proba = np.asarray(y_true), np.asarray(proba)
    for cls in (0, 1):
        ax.hist(proba[y_true == cls], bins=25, alpha=.7,
                color=PALETTE[cls], label=f"Actual: {LABELS[cls]}")
    ax.axvline(.30, color="grey", ls=":"); ax.axvline(.70, color="grey", ls=":")
    top = ax.get_ylim()[1] * .92
    for x, t in ((.15, "Low"), (.50, "Medium"), (.85, "High")):
        ax.text(x, top, t, ha="center")
    ax.set_xlabel("Predicted fraud probability (Random Forest)")
    ax.set_ylabel("Transactions"); ax.set_title("Fraud-risk score distribution")
    ax.legend(loc="center left")
    fig.tight_layout(); return fig
