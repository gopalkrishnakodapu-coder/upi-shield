"""UPI Fraud Detection & Risk Analysis -- Streamlit app.

Run:  streamlit run app.py
"""
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src import visualize as viz
from src.config import FEATURES, FIG_DIR, MODELS_DIR, REPORTS_DIR, TARGET
from src.data import load_data
from src.predict import load_models, predict_transaction

st.set_page_config(page_title="UPI Fraud Detection", page_icon="🛡️", layout="wide")


# ------------------------------------------------------------------ caching
@st.cache_data
def get_data() -> pd.DataFrame:
    return load_data()


@st.cache_resource
def get_models():
    """Load saved models; train them first if they are missing."""
    if not (MODELS_DIR / "random_forest.joblib").exists():
        from src.train import main as train_main
        train_main()
    return load_models()


def show(fig):
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)


df = get_data()
models = get_models()

# ------------------------------------------------------------------- header
st.title("🛡️ UPI Fraud Detection & Risk Analysis")
st.caption("Random Forest vs Logistic Regression on UPI transaction data, "
           "with transaction analysis and live risk scoring.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{len(df):,}")
c2.metric("Fraud-risk rate", f"{df[TARGET].mean():.1%}")
c3.metric("Avg amount", f"{df['trans_amount'].mean():,.0f}")
c4.metric("Median amount (fraud)", f"{df.loc[df[TARGET] == 1, 'trans_amount'].median():,.0f}")

tab_analysis, tab_models, tab_predict = st.tabs(
    ["📊 Transaction analysis", "🤖 Model comparison", "🔮 Predict a transaction"])

# ------------------------------------------------------ transaction analysis
with tab_analysis:
    st.subheader("What do fraudulent transactions look like?")
    a, b = st.columns(2)
    with a:
        show(viz.plot_amount_distribution(df))
        show(viz.plot_fraud_by_hour(df))
    with b:
        show(viz.plot_fraud_by_amount_band(df))
        show(viz.plot_fraud_by_category(df))
    a, b = st.columns(2)
    with a:
        show(viz.plot_hour_amount_heatmap(df))
    with b:
        show(viz.plot_fraud_by_age_group(df))

    with st.expander("Browse / filter the raw data"):
        lo, hi = float(df.trans_amount.min()), float(df.trans_amount.max())
        amt = st.slider("Amount range", lo, hi, (lo, hi))
        only_fraud = st.checkbox("Show only fraud-risk transactions")
        view = df[df.trans_amount.between(*amt)]
        if only_fraud:
            view = view[view[TARGET] == 1]
        st.write(f"{len(view):,} transactions")
        st.dataframe(view, use_container_width=True)

# ----------------------------------------------------------- model comparison
with tab_models:
    st.subheader("Random Forest vs Logistic Regression (held-out test set)")
    metrics_path = REPORTS_DIR / "metrics.csv"
    if metrics_path.exists():
        metrics = pd.read_csv(metrics_path, index_col=0)
        st.dataframe(metrics.style.format("{:.3f}").highlight_max(axis=0, color="#cfe8cf"),
                     use_container_width=True)
        a, b = st.columns(2)
        with a:
            show(viz.plot_metric_comparison(metrics))
        with b:
            st.image(str(FIG_DIR / "11_roc_curves.png"))
        st.image(str(FIG_DIR / "09_confusion_matrices.png"))
        st.subheader("Feature importance")
        st.image(str(FIG_DIR / "12_feature_importance.png"))
        st.subheader("Fraud-risk score distribution")
        st.image(str(FIG_DIR / "13_risk_score_distribution.png"))
    else:
        st.warning("Run `python -m src.train` to generate metrics and figures.")

# ------------------------------------------------------------------- predict
with tab_predict:
    st.subheader("Score a new transaction")
    with st.form("txn"):
        a, b, c = st.columns(3)
        amount = a.number_input("Amount", 0.0, 10000.0, 350.0, step=10.0)
        hour = b.slider("Hour of day", 0, 23, 14)
        age = c.slider("Customer age", 14, 100, 35)
        a, b, c = st.columns(3)
        day = a.slider("Day of month", 1, 31, 15)
        month = b.slider("Month", 1, 12, 6)
        category = c.selectbox("Category code", sorted(df["category"].unique()))
        state = st.selectbox("State code", sorted(df["state"].unique()))
        go = st.form_submit_button("Assess risk", type="primary")

    if go:
        txn = {"trans_hour": hour, "trans_day": day, "trans_month": month,
               "category": category, "age": age, "trans_amount": amount,
               "state": state}
        results = predict_transaction(models, txn)
        rf = results["Random Forest"]
        colour = {"Low": "green", "Medium": "orange", "High": "red"}[rf["risk"]]

        st.markdown(f"### Risk level: :{colour}[{rf['risk']}]")
        st.progress(min(rf["probability"], 1.0),
                    text=f"Random Forest fraud probability: {rf['probability']:.1%}")

        a, b = st.columns(2)
        for col, (name, res) in zip((a, b), results.items()):
            col.metric(name, f"{res['probability']:.1%}",
                       "Flagged as fraud" if res["prediction"] else "Looks legitimate",
                       delta_color="inverse" if res["prediction"] else "normal")
        st.caption("Risk bands: Low < 30%, Medium 30-70%, High > 70% fraud probability. "
                   "Models are trained on a small dataset -- this is a "
                   "demo, not a production fraud system.")
