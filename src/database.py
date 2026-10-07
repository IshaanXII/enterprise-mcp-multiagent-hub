"""SQLite enterprise DB — WHY SQLite: brief allows SQLite/PostgreSQL, zero-setup for demo + docker."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "enterprise.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers(customer_id TEXT PRIMARY KEY, name TEXT, email TEXT, tier TEXT, status TEXT, fraud_flag INTEGER);
CREATE TABLE IF NOT EXISTS orders(order_id TEXT PRIMARY KEY, customer_id TEXT, amount REAL, status TEXT, item TEXT);
CREATE TABLE IF NOT EXISTS disputes(dispute_id TEXT PRIMARY KEY, customer_id TEXT, order_id TEXT, reason TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS tickets(ticket_id TEXT PRIMARY KEY, customer_id TEXT, text TEXT, category TEXT, priority TEXT, status TEXT, resolution TEXT);
CREATE TABLE IF NOT EXISTS refunds(refund_id TEXT PRIMARY KEY, order_id TEXT, amount REAL, status TEXT);
"""

SEED_CUSTOMERS = [
    ("CUST-001", "Aarav Sharma", "aarav@acme.com", "Enterprise", "active", 0),
    ("CUST-002", "Diya Patel", "diya@acme.com", "SMB", "active", 0),
    ("CUST-003", "Kabir Singh", "kabir@acme.com", "Enterprise", "suspended", 1),
    ("CUST-004", "Meera Iyer", "meera@acme.com", "Startup", "active", 0),
]
SEED_ORDERS = [
    ("ORD-1001", "CUST-001", 1200.0, "delivered", "Laptop x2"),
    ("ORD-1002", "CUST-002", 349.0, "delivered", "SaaS annual"),
    ("ORD-1003", "CUST-003", 2500.0, "delivered", "Server rack"),
    ("ORD-1004", "CUST-004", 99.0, "pending", "Support pack"),
]
SEED_DISPUTES = [
    ("DSP-01", "CUST-002", "ORD-1002", "duplicate charge", "open"),
    ("DSP-02", "CUST-003", "ORD-1003", "overcharge", "open"),
    ("DSP-03", "CUST-003", "ORD-1003", "late delivery", "open"),
]

# ---- 500-customer scale-up (deterministic, no extra deps) ----
FIRST = ["Aarav","Diya","Kabir","Meera","Rohan","Ananya","Vikram","Sneha","Arjun","Priya","Karan","Neha","Aditya","Pooja","Rahul","Ishita","Manav","Riya","Dev","Kavya"]
LAST = ["Sharma","Patel","Singh","Iyer","Gupta","Mehta","Nair","Reddy","Khan","Das","Kulkarni","Joshi","Chopra","Verma","Agarwal"]
ITEMS = ["Laptop x1","Monitor 27in","SaaS annual","Support pack","Server rack","Keyboard set","Cloud credits $500","Headset x5","Docking station","License 10-seat"]
REASONS = ["duplicate charge","overcharge","late delivery","damaged item","wrong item","service downtime"]

def _gen_bulk():
    import random
    random.seed(42)  # deterministic so tests/demo stable
    custs, orders, disputes = [], [], []
    for i in range(5, 501):
        cid = f"CUST-{i:03d}"
        name = f"{random.choice(FIRST)} {random.choice(LAST)}{i}"
        tier = random.choices(["Enterprise","SMB","Startup"], weights=[2,5,3])[0]
        suspended = random.random() < 0.06
        fraud = 1 if (suspended and random.random() < 0.5) else 0
        custs.append((cid, name, f"user{i}@acme.com", tier, "suspended" if suspended else "active", fraud))
        oid = f"ORD-{1000+i}"
        amt = round(random.choice([49,99,199,349,499,799,1200,2500,5000]) + random.random()*20, 2)
        orders.append((oid, cid, amt, random.choices(["delivered","pending","shipped"], weights=[7,2,1])[0], random.choice(ITEMS)))
        if random.random() < 0.22:
            disputes.append((f"DSP-{i:04d}", cid, oid, random.choice(REASONS), "open"))
    return custs, orders, disputes

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH))

def seed():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.executemany("INSERT OR REPLACE INTO customers VALUES(?,?,?,?,?,?)", SEED_CUSTOMERS)
    cur.executemany("INSERT OR REPLACE INTO orders VALUES(?,?,?,?,?)", SEED_ORDERS)
    cur.executemany("INSERT OR REPLACE INTO disputes VALUES(?,?,?,?,?)", SEED_DISPUTES)
    bulk_c, bulk_o, bulk_d = _gen_bulk()
    cur.executemany("INSERT OR REPLACE INTO customers VALUES(?,?,?,?,?,?)", bulk_c)
    cur.executemany("INSERT OR REPLACE INTO orders VALUES(?,?,?,?,?)", bulk_o)
    cur.executemany("INSERT OR REPLACE INTO disputes VALUES(?,?,?,?,?)", bulk_d)
    n = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.commit()
    conn.close()
    return f"{DB_PATH} ({n} customers)"

# ---- MCP tool backends (imported by mcp_server + mcp_client) ----
def db_get_customer(customer_id: str) -> dict:
    conn = get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM customers WHERE customer_id=?", (customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else {"error": "customer not found"}

def db_get_orders(customer_id: str) -> list:
    conn = get_conn(); conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM orders WHERE customer_id=?", (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_get_disputes(customer_id: str) -> list:
    conn = get_conn(); conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM disputes WHERE customer_id=?", (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_create_refund(order_id: str, amount: float) -> dict:
    import uuid
    rid = f"RFD-{uuid.uuid4().hex[:6].upper()}"
    conn = get_conn()
    conn.execute("INSERT INTO refunds VALUES(?,?,?,?)", (rid, order_id, amount, "initiated"))
    conn.commit(); conn.close()
    return {"refund_id": rid, "order_id": order_id, "amount": amount, "status": "initiated"}

def db_log_ticket(ticket_id: str, customer_id: str, text: str, category: str, priority: str, status: str, resolution: str):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO tickets VALUES(?,?,?,?,?,?,?)",
                 (ticket_id, customer_id, text, category, priority, status, resolution))
    conn.commit(); conn.close()
