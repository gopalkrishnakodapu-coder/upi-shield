"""
UPI Fraud Detection API
FastAPI backend for model inference and dashboard data.
"""
from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import FEATURES, TARGET, REPORTS_DIR, MODELS_DIR, risk_level
from src.data import load_data
from src.predict import load_models, predict_transaction

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND = BASE_DIR / "frontend" / "static"

app = FastAPI(
    title="UPI Fraud Detection API",
    version="1.0.0",
    description="Machine-learning API for UPI transaction fraud-risk assessment."
)

@app.middleware("http")
async def no_cache(request, call_next):
    r = await call_next(request)
    if not request.url.path.startswith(("/api", "/ocr", "/reports")):
        r.headers["Cache-Control"] = "no-cache"
    return r


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

df = load_data()
models = load_models()

from backend import db, payments, admin
db.init()
payments.models = models
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")  # fixes dashboard images
app.include_router(payments.router)
app.include_router(admin.router)

class Transaction(BaseModel):
    trans_hour: int = Field(..., ge=0, le=23)
    trans_day: int = Field(..., ge=1, le=31)
    trans_month: int = Field(..., ge=1, le=12)
    category: int
    age: int = Field(..., ge=14, le=100)
    trans_amount: float = Field(..., ge=0)
    state: int

@app.get("/")
def home():
    return FileResponse(FRONTEND / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "upi-fraud-detection-api", "models_loaded": True}

@app.get("/api/stats")
def stats():
    return {
        "transactions": int(len(df)),
        "fraud_risk_rate": round(float(df[TARGET].mean()), 4),
        "average_amount": round(float(df["trans_amount"].mean()), 2),
        "median_fraud_amount": round(float(df.loc[df[TARGET] == 1, "trans_amount"].median()), 2),
        "categories": sorted(df["category"].unique().astype(int).tolist()),
        "states": sorted(df["state"].unique().astype(int).tolist()),
        "amount_min": float(df["trans_amount"].min()),
        "amount_max": float(df["trans_amount"].max())
    }

@app.get("/api/models")
def model_metrics():
    path = REPORTS_DIR / "metrics.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Model metrics not found.")
    metrics = pd.read_csv(path)
    return metrics.to_dict(orient="records")

@app.get("/api/feature-importance")
def feature_importance():
    path = REPORTS_DIR / "feature_importance.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Feature importance report not found.")
    return pd.read_csv(path).round(4).to_dict(orient="records")

@app.get("/api/transactions")
def transactions(
    limit: int = Query(50, ge=1, le=500),
    fraud_only: bool = False,
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
):
    view = df.copy()
    if fraud_only:
        view = view[view[TARGET] == 1]
    if min_amount is not None:
        view = view[view["trans_amount"] >= min_amount]
    if max_amount is not None:
        view = view[view["trans_amount"] <= max_amount]
    return view.head(limit).to_dict(orient="records")

@app.post("/api/predict")
def predict(txn: Transaction):
    payload = txn.model_dump()
    results = predict_transaction(models, payload)
    rf = results["Random Forest"]
    return {
        "random_forest": rf,
        "logistic_regression": results["Logistic Regression"],
        "risk_score": round(rf["probability"] * 100, 2),
        "risk_level": rf["risk"],
        "recommendation": (
            "Review or block the transaction for further verification."
            if rf["risk"] == "High"
            else "Request additional verification if required."
            if rf["risk"] == "Medium"
            else "Transaction has a lower predicted fraud risk."
        )
    }

# Serve frontend assets from the same deployed service.
@app.get("/{path:path}")
def frontend_assets(path: str):
    requested = FRONTEND / path
    if requested.is_file():
        return FileResponse(requested)
    return FileResponse(FRONTEND / "index.html")
