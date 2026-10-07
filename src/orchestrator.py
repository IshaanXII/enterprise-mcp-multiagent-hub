"""Orchestrator — WHY LangGraph-pattern in plain Python: explicit nodes
triage -> crm_lookup (MCP) -> rag_retrieve -> resolve -> act/log with error recovery.
Gives you Tool Calling + Memory + Fallback marks without heavy deps."""
import uuid, json, datetime
from pathlib import Path
from src.triage_agent import triage
from src import mcp_client
from src.rag_store import retrieve
from src.resolution_agent import resolve
from src.escalation_agent import escalate

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)

def run_ticket(text: str, customer_id: str) -> dict:
    mcp_client.TOOL_LOG.clear()  # per-ticket tool trace for clean Loom demo
    trace = {"ticket_id": f"T-{uuid.uuid4().hex[:6].upper()}", "input": text, "customer_id": customer_id}
    try:
        # Node 1: triage
        tr = triage(text); trace["triage"] = tr
        # Node 2: CRM via MCP (with fallback)
        try:
            cust = mcp_client.call("get_customer", customer_id=customer_id)
            orders = mcp_client.call("get_orders", customer_id=customer_id)
            disputes = mcp_client.call("get_disputes", customer_id=customer_id)
        except Exception as e:
            trace["crm_error"] = str(e)
            cust, orders, disputes = {"customer_id": customer_id, "status": "unknown"}, [], []
        trace["crm"] = {"customer": cust, "orders": orders, "disputes": disputes}
        # Node 3: RAG
        rag_docs, rag_backend = retrieve(f"{tr['category']} {text}")
        trace["rag_backend"] = rag_backend
        trace["rag_docs"] = [{"source": d.get("source"), "score": round(float(d.get("score", 0)), 3),
                                "excerpt": d.get("text", "")[:500]} for d in rag_docs]
        # Node 4: resolve
        res = resolve(text, tr, cust, orders, disputes, rag_docs)
        trace["resolution"] = res
        # Node 5: act + memory
        if res["action"]["type"] == "auto_refund":
            rf = mcp_client.call("create_refund", order_id=res["action"]["refund"]["order_id"], amount=res["action"]["refund"]["amount"])
            trace["refund"] = rf
            # Inject REAL refund ID from tool (replaces any placeholder)
            res["draft"] = res["draft"].replace("[system-refund-id]", rf["refund_id"])
            if "[system-refund-id]" not in res["draft"] and "Refund will be initiated" in res["draft"]:
                res["draft"] += f" [Refund {rf['refund_id']} initiated]"
            trace["resolution"] = res
            status = "auto_resolved"
        elif res["action"].get("approval_needed"):
            status = "needs_approval"
            trace["refund"] = None
        else:
            status = "drafted"
            trace["refund"] = None
        mcp_client.call("log_ticket", ticket_id=trace["ticket_id"], customer_id=customer_id,
                        text=text, category=tr["category"], priority=tr["priority"],
                        status=status, resolution=res["draft"])
        trace["status"] = status
        # Node 6: escalation (multi-agent handoff)
        try:
            esc = escalate(trace["ticket_id"], tr, cust, res)
        except Exception as e:
            esc = {"escalated": False, "reasons": [], "page": "", "error": str(e)}
        trace["escalation"] = esc
        trace["tools"] = mcp_client.last_tools()
    except Exception as e:
        # Global fallback — never crash live demo
        trace["status"] = "error_fallback"
        trace["error"] = str(e)
        trace["resolution"] = {"draft": f"System error logged. Human will review within SLA. ({e})",
                               "action": {"type": "draft_reply"}, "backend": "error-fallback"}
    # Persist trace for Loom evidence
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    (LOG_DIR / f"trace_{trace['ticket_id']}_{ts}.json").write_text(json.dumps(trace, indent=2))
    return trace

if __name__ == "__main__":
    import sys
    print(json.dumps(run_ticket(sys.argv[1] if len(sys.argv) > 1 else "I was double charged $349, please refund urgently",
                                sys.argv[2] if len(sys.argv) > 2 else "CUST-002"), indent=2))
