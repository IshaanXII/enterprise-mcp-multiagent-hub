"""Analytics Agent — WHY: data-driven decisions (CLO2): SLA risk, refund leakage, workload.
Reads SQLite tickets/refunds directly — no LLM needed, always works."""
import sqlite3
from src.database import get_conn

SLA_HOURS = {"P1": 4, "P2": 8, "P3": 24, "P4": 72}

def overview() -> dict:
    conn = get_conn(); conn.row_factory = sqlite3.Row
    tickets = [dict(r) for r in conn.execute("SELECT category,priority,status FROM tickets").fetchall()]
    refunds = [dict(r) for r in conn.execute("SELECT amount FROM refunds").fetchall()]
    conn.close()
    by_status: dict = {}
    by_priority: dict = {}
    for t in tickets:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1
    total_refund = round(sum(r["amount"] for r in refunds), 2)
    # SLA risk: needs_approval + P1/P2 backlog approximate breach risk
    at_risk = by_status.get("needs_approval", 0) + by_priority.get("P1", 0)
    return {
        "tickets_total": len(tickets),
        "by_status": by_status,
        "by_priority": by_priority,
        "refunds_count": len(refunds),
        "refunds_total": total_refund,
        "sla_hours": SLA_HOURS,
        "at_risk_count": at_risk,
        "note": "needs_approval + P1 backlog = breach risk; auto_resolved share = automation rate.",
    }
