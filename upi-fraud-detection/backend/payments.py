"""Simulated UPI wallet API: auth, payee check, pay (with fraud decision), history, reports."""
import json, secrets, time
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from . import db, risk

router = APIRouter(prefix="/api")
models = None   # set from main.py

class Reg(BaseModel):
    name: str
    upi_id: str
    password: str = Field(min_length=6)
class Login(BaseModel):
    upi_id: str
    password: str
class Pay(BaseModel):
    to: str
    amount: float = Field(gt=0, le=100000)
    password: Optional[str] = None      # acts as the UPI PIN for Medium-risk payments
class Assess(BaseModel):
    to: str
    amount: float = Field(gt=0, le=100000)
class Report(BaseModel):
    upi_id: str
    reason: str = "Suspected fraud"

def me(auth):
    token = (auth or "").replace("Bearer ", "")
    with db.conn() as c:
        u = c.execute("SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=?", (token,)).fetchone()
    if not u:
        raise HTTPException(401, "Please log in")
    return u

def session(c, uid):
    t = secrets.token_hex(16)
    c.execute("INSERT INTO sessions VALUES(?,?)", (t, uid))
    return t

@router.post("/auth/register")
def register(b: Reg):
    upi = b.upi_id.strip().lower()
    if "@" not in upi:
        raise HTTPException(400, "UPI ID must look like name@bank")
    with db.conn() as c:
        if c.execute("SELECT 1 FROM users WHERE upi_id=?", (upi,)).fetchone():
            raise HTTPException(400, "UPI ID already taken")
        db.create_user(c, b.name, upi, b.password)
        uid = c.execute("SELECT id FROM users WHERE upi_id=?", (upi,)).fetchone()[0]
        return {"token": session(c, uid)}

@router.post("/auth/login")
def login(b: Login):
    with db.conn() as c:
        u = c.execute("SELECT * FROM users WHERE upi_id=?", (b.upi_id.strip().lower(),)).fetchone()
        if not u or db.hash_pw(b.password, u["salt"]) != u["pw"]:
            raise HTTPException(401, "Wrong UPI ID or password")
        return {"token": session(c, u["id"])}

@router.get("/me")
def profile(authorization: str = Header(None)):
    u = me(authorization)
    return {"name": u["name"], "upi_id": u["upi_id"], "balance": u["balance"]}

@router.get("/payee/check")
def payee_check(upi_id: str, authorization: str = Header(None)):
    me(authorization)
    upi = upi_id.strip().lower()
    with db.conn() as c:
        u = c.execute("SELECT name FROM users WHERE upi_id=?", (upi,)).fetchone()
        reports, senders = risk.payee_stats(c, upi)
    pts, why = risk.payee_rules(reports, senders)
    return {"exists": bool(u), "name": u["name"] if u else None,
            "risk_level": risk.level(pts * 1.5), "reports": reports, "reasons": why}

@router.post("/pay")
def pay(b: Pay, authorization: str = Header(None)):
    u = me(authorization)
    to = b.to.strip().lower()
    with db.conn() as c:
        r = c.execute("SELECT * FROM users WHERE upi_id=?", (to,)).fetchone()
        if not r or to == u["upi_id"]:
            raise HTTPException(400, "Payee not found" if not r else "You cannot pay yourself")
        if b.amount > u["balance"]:
            raise HTTPException(400, "Insufficient balance")
        a = risk.assess(c, models, u["upi_id"], to, b.amount)
        out = {"risk_level": a["level"], "risk_score": a["score"], "ml_probability": a["ml"], "reasons": a["reasons"]}
        if a["level"] == "Medium" and not (b.password and db.hash_pw(b.password, u["salt"]) == u["pw"]):
            return {**out, "status": "confirm_required",
                    "message": "Medium risk. Enter your PIN (password) to confirm."}
        status = "blocked" if a["level"] == "High" else "completed"
        if status == "completed":
            c.execute("UPDATE users SET balance=balance-? WHERE id=?", (b.amount, u["id"]))
            c.execute("UPDATE users SET balance=balance+? WHERE id=?", (b.amount, r["id"]))
        c.execute("INSERT INTO txns(sender,receiver,amount,ts,score,ml,level,status,reasons) VALUES(?,?,?,?,?,?,?,?,?)",
                  (u["upi_id"], to, b.amount, time.time(), a["score"], a["ml"], a["level"], status, json.dumps(a["reasons"])))
        return {**out, "status": status,
                "message": "Payment sent." if status == "completed" else "Payment blocked: high fraud risk."}

@router.get("/history")
def history(authorization: str = Header(None)):
    u = me(authorization)
    with db.conn() as c:
        rows = c.execute("SELECT * FROM txns WHERE sender=? OR receiver=? ORDER BY id DESC LIMIT 50",
                         (u["upi_id"], u["upi_id"])).fetchall()
    return [{**dict(r), "reasons": json.loads(r["reasons"])} for r in rows]

@router.post("/report")
def report(b: Report, authorization: str = Header(None)):
    u = me(authorization)
    with db.conn() as c:
        c.execute("INSERT INTO reports VALUES(?,?,?,?)", (b.upi_id.strip().lower(), u["upi_id"], b.reason, time.time()))
    return {"ok": True}

@router.get("/admin/flagged")
def flagged():
    """Demo-only: add admin auth before any real use."""
    with db.conn() as c:
        txns = c.execute("SELECT * FROM txns WHERE level!='Low' ORDER BY id DESC LIMIT 50").fetchall()
        nums = c.execute("SELECT upi_id, COUNT(DISTINCT reporter) n FROM reports GROUP BY upi_id ORDER BY n DESC").fetchall()
    return {"flagged_transactions": [dict(r) for r in txns], "reported_numbers": [dict(r) for r in nums]}


@router.post("/risk/assess")
def assess_only(b: Assess, authorization: str = Header(None)):
    """Risk score for ANY UPI ID + amount. Moves no money (used before opening GPay/PhonePe/Paytm)."""
    u = me(authorization)
    to = b.to.strip().lower()
    if "@" not in to or len(to) < 5:
        raise HTTPException(400, "Enter a valid UPI ID, e.g. name@bank")
    with db.conn() as c:
        r = c.execute("SELECT name FROM users WHERE upi_id=?", (to,)).fetchone()
        a = risk.assess(c, models, u["upi_id"], to, b.amount)
    return {"risk_level": a["level"], "risk_score": a["score"], "ml_probability": a["ml"],
            "reasons": a["reasons"], "payee_name": r["name"] if r else None, "known": bool(r)}
