"""Admin profile + dashboard scanner endpoints.

Set these environment variables (e.g. on Render) to show your real details:
ADMIN_NAME, ADMIN_ROLE, ADMIN_EMAIL, ADMIN_PHONE, ADMIN_ORG
NOTE: demo-only - the dashboard has no login. Add authentication before real use.
"""
import os, time
from fastapi import APIRouter
from . import db, risk

router = APIRouter(prefix="/api")
STARTED = time.time()


@router.get("/admin/profile")
def admin_profile():
    with db.conn() as c:
        one = lambda q: c.execute(q).fetchone()[0]
        stats = {
            "wallet_users": one("SELECT COUNT(*) FROM users"),
            "payments": one("SELECT COUNT(*) FROM txns"),
            "flagged_payments": one("SELECT COUNT(*) FROM txns WHERE level!='Low'"),
            "blocked_payments": one("SELECT COUNT(*) FROM txns WHERE status='blocked'"),
            "reported_ids": one("SELECT COUNT(DISTINCT upi_id) FROM reports"),
        }
    return {
        "name": os.getenv("ADMIN_NAME", "Admin"),
        "role": os.getenv("ADMIN_ROLE", "Fraud Analyst · Administrator"),
        "email": os.getenv("ADMIN_EMAIL", "admin@upishield.example"),
        "phone": os.getenv("ADMIN_PHONE", "Not set"),
        "organization": os.getenv("ADMIN_ORG", "UPI Shield"),
        "access": "Full access",
        "uptime_minutes": int((time.time() - STARTED) / 60),
        "version": "1.0.0",
        "stats": stats,
    }


@router.get("/scan/payee")
def scan_payee(upi_id: str):
    """Payee lookup used by the dashboard screenshot scanner (no login)."""
    upi = upi_id.strip().lower()
    with db.conn() as c:
        u = c.execute("SELECT name FROM users WHERE upi_id=?", (upi,)).fetchone()
        reports, senders = risk.payee_stats(c, upi)
    pts, why = risk.payee_rules(reports, senders)
    return {"exists": bool(u), "name": u["name"] if u else None,
            "risk_level": risk.level(pts * 1.5), "reports": reports, "reasons": why}
