"""Train both models, evaluate on a held-out test set, and save the models,
metrics and every report figure.

Run from the project root:  python -m src.train
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, classification_report, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import cross_val_score, StratifiedKFold

from . import visualize as viz
from .config import (FEATURES, FIG_DIR, MODELS_DIR, RANDOM_STATE, REPORTS_DIR)
from .data import load_data, split_data
from .models import build_logistic_regression, build_random_forest


def evaluate(name, model, X_test, y_test):
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    return {
        "model": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
    }, pred, proba


def save(fig, name):
    fig.savefig(FIG_DIR / name, dpi=150, bbox_inches="tight")
    viz.plt.close(fig)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    X_train, X_test, y_train, y_test = split_data(df)
    print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows")

    models = {
        "Random Forest": build_random_forest(),
        "Logistic Regression": build_logistic_regression(),
    }

    rows, preds, probas, cv = [], {}, {}, {}
    skf = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    for name, model in models.items():
        scores = cross_val_score(model, X_train, y_train, cv=skf, scoring="f1")
        cv[name] = (scores.mean(), scores.std())
        model.fit(X_train, y_train)
        row, pred, proba = evaluate(name, model, X_test, y_test)
        row["cv_f1_mean"], row["cv_f1_std"] = cv[name]
        rows.append(row); preds[name] = pred; probas[name] = proba
        print(f"\n=== {name} ===  (5-fold CV F1: {cv[name][0]:.3f} +/- {cv[name][1]:.3f})")
        print(classification_report(y_test, pred, target_names=["Legit", "Fraud"]))

    metrics = pd.DataFrame(rows).set_index("model")
    metrics.round(4).to_csv(REPORTS_DIR / "metrics.csv")
    (REPORTS_DIR / "metrics.json").write_text(
        json.dumps(metrics.round(4).to_dict("index"), indent=2))
    print("\n", metrics.round(3).to_string())

    for name, model in models.items():
        joblib.dump(model, MODELS_DIR / f"{name.lower().replace(' ', '_')}.joblib")

    # ------------------------------------------------------------- figures
    save(viz.plot_class_balance(df), "01_class_balance.png")
    save(viz.plot_amount_distribution(df), "02_amount_distribution.png")
    save(viz.plot_fraud_by_amount_band(df), "03_fraud_by_amount_band.png")
    save(viz.plot_fraud_by_hour(df), "04_fraud_by_hour.png")
    save(viz.plot_fraud_by_category(df), "05_fraud_by_category.png")
    save(viz.plot_fraud_by_age_group(df), "06_fraud_by_age_group.png")
    save(viz.plot_hour_amount_heatmap(df), "07_hour_amount_heatmap.png")
    save(viz.plot_correlation(df, FEATURES), "08_correlation.png")

    save(viz.plot_confusion_matrices(
        {n: (y_test, p) for n, p in preds.items()}), "09_confusion_matrices.png")
    save(viz.plot_metric_comparison(metrics), "10_metric_comparison.png")
    save(viz.plot_roc_curves(
        {n: (y_test, p) for n, p in probas.items()}), "11_roc_curves.png")

    rf = models["Random Forest"]
    perm = permutation_importance(rf, X_test, y_test, scoring="f1", n_repeats=15,
                                  random_state=RANDOM_STATE, n_jobs=-1)
    impurity = rf.named_steps["model"].feature_importances_
    save(viz.plot_feature_importance(FEATURES, impurity, perm.importances_mean),
         "12_feature_importance.png")
    pd.DataFrame({"feature": FEATURES, "impurity_importance": impurity,
                  "permutation_importance": perm.importances_mean}
                 ).sort_values("permutation_importance", ascending=False
                 ).round(4).to_csv(REPORTS_DIR / "feature_importance.csv", index=False)

    save(viz.plot_risk_score_distribution(y_test, probas["Random Forest"]),
         "13_risk_score_distribution.png")
    print(f"\nSaved models to {MODELS_DIR} and figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
