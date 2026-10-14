# Deployment checklist

## Local test
1. `python -m venv .venv`
2. Windows: `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `uvicorn backend.main:app --host 127.0.0.1 --port 8000`
5. Open `http://127.0.0.1:8000`

## Render
1. Push the whole project folder to GitHub.
2. Create a new Web Service in Render and select the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Deploy and open the generated HTTPS URL.

## Presentation demo
1. Open the dashboard and show transaction count and fraud-risk rate.
2. Open Model Performance and explain RF vs LR metrics.
3. Open Risk Assessment.
4. Enter amount ₹850, hour 2, age 35, day 14, month 6 and select category 4/state 22.
5. Click Assess Fraud Risk and show the returned probability/risk.
6. Explain that the dataset is academic/synthetic-like and that production deployment needs realistic class imbalance and additional behavioural features.

## Important
The dataset has 59.19% fraud labels. Do not claim that the model will achieve 95.88% accuracy on real UPI traffic.

## Dashboard icons (top-right)
- Scanner icon: upload a payment screenshot; the app reads amount, UPI ID, reference, date and status, then gives a fraud verdict. Same scanner is in the pay app (Home > Scan screenshot).
- Admin icon: shows the admin profile and system stats. Edit your name, role, email and phone in Render > Environment (ADMIN_NAME, ADMIN_ROLE, ADMIN_EMAIL, ADMIN_PHONE, ADMIN_ORG).
- The dashboard has no login. Add authentication before using it with real data.
