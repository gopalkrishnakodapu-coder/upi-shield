"""SQLite storage for the simulated UPI wallet (virtual money only)."""
import hashlib, secrets, sqlite3, time
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "upi_app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, upi_id TEXT UNIQUE,
  pw TEXT, salt TEXT, balance REAL, created REAL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER);
CREATE TABLE IF NOT EXISTS txns(id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, amount REAL,
  ts REAL, score REAL, ml REAL, level TEXT, status TEXT, reasons TEXT);
CREATE TABLE IF NOT EXISTS reports(upi_id TEXT, reporter TEXT, reason TEXT, ts REAL);
"""

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def hash_pw(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 100_000).hex()

def create_user(c, name, upi, pw, balance=10000.0):
    salt = secrets.token_hex(8)
    c.execute("INSERT INTO users(name,upi_id,pw,salt,balance,created) VALUES(?,?,?,?,?,?)",
              (name, upi.lower(), hash_pw(pw, salt), salt, balance, time.time()))

def init():
    with conn() as c:
        c.executescript(SCHEMA)
        _seed = True
        if not c.execute("SELECT 1 FROM users").fetchone():
            for n, u in [("Alice", "alice@upi"), ("Bob", "bob@upi"),
                         ("Fresh Mart", "shop@upi"), ("Lucky Prize", "lucky.prize@upi")]:
                create_user(c, n, u, "demo123", 50000)
            for i in range(4):   # demo scam number already reported by 4 users
                c.execute("INSERT INTO reports VALUES(?,?,?,?)",
                          ("lucky.prize@upi", f"seed{i}", "Fake prize scam", time.time()))

BILLERS = [("Mobile Recharge","mobile@bills"),("DTH Recharge","dth@bills"),("Electricity Board","electricity@bills"),
           ("Credit Card Bill","creditcard@bills"),("EMI Payments","emi@bills"),("Insurance Premium","insurance@bills"),
           ("Google Play Recharge","googleplay@bills")]

def seed_billers():
    with conn() as c:
        for n, u in BILLERS:
            if not c.execute("SELECT 1 FROM users WHERE upi_id=?", (u,)).fetchone():
                create_user(c, n, u, secrets.token_hex(8), 0)

_init_orig = init
def init():
    _init_orig()
    seed_billers()
