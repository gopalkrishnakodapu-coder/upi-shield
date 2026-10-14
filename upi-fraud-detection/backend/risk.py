"""Risk engine: behaviour rules (main signal) + ML model score (supporting signal)."""
import datetime, time
from src.predict import predict_transaction

LOW_MAX, MED_MAX = 35, 65          # score < 35 Low, < 65 Medium, else High
ML_WEIGHT = 0.25                    # dataset is synthetic (59% fraud) so ML is only a hint

def payee_stats(c, upi):
    reports = c.execute("SELECT COUNT(DISTINCT reporter) FROM reports WHERE upi_id=?", (upi,)).fetchone()[0]
    senders = c.execute("SELECT COUNT(DISTINCT sender) FROM txns WHERE receiver=? AND ts>? AND status='completed'",
                        (upi, time.time() - 86400)).fetchone()[0]
    return reports, senders

def payee_rules(reports, senders):
    pts, why = 0, []
    if reports:
        pts += min(45, 15 * reports); why.append(f"Reported as fraud by {reports} user(s)")
    if senders >= 5:
        pts += 25; why.append(f"Received money from {senders} different people in 24h (possible mule account)")
    return pts, why

def level(score):
    return "Low" if score < LOW_MAX else "Medium" if score < MED_MAX else "High"

def assess(c, models, sender, receiver, amount):
    now, t = time.time(), datetime.datetime.now()
    pts, why = payee_rules(*payee_stats(c, receiver))
    avg = c.execute("SELECT AVG(amount) FROM txns WHERE sender=? AND status='completed'", (sender,)).fetchone()[0]
    prior = c.execute("SELECT COUNT(*) FROM txns WHERE sender=? AND receiver=? AND status='completed'",
                      (sender, receiver)).fetchone()[0]
    velocity = c.execute("SELECT COUNT(*) FROM txns WHERE sender=? AND ts>?", (sender, now - 600)).fetchone()[0]

    if amount > 25000:   pts += 35; why.append("Very high amount (over ₹25,000)")
    elif amount > 2000:  pts += 15; why.append("High amount (over ₹2,000)")
    if avg and amount > 3 * avg:
        pts += 20; why.append(f"More than 3x your usual payment (avg ₹{avg:,.0f})")
    if prior == 0 and amount > 1000:
        pts += 15; why.append("First payment to this person")
    if prior == 0 and t.hour < 6:
        pts += 10; why.append("Night-time payment to a new payee")
    if velocity >= 5:
        pts += 25; why.append("Many payments in the last 10 minutes")

    ml = predict_transaction(models, {"trans_hour": t.hour, "trans_day": t.day, "trans_month": t.month,
                                      "category": 4, "age": 35, "trans_amount": amount,
                                      "state": 22})["Random Forest"]["probability"]
    score = round(min(100, pts + ML_WEIGHT * ml * 100), 1)
    return {"score": score, "ml": round(ml, 3), "level": level(score), "reasons": why}
