from src.orchestrator import run_ticket
from src.database import seed
from src.rag_store import ingest_chroma_if_available

def setup_module(m):
    seed(); ingest_chroma_if_available()

def test_billing_auto_refund():
    tr = run_ticket("double charged $349 refund urgently", "CUST-002")
    assert tr["triage"]["category"] == "billing"
    assert tr["status"] in ("auto_resolved", "needs_approval", "drafted")
    assert "FIN-001" in tr["resolution"]["draft"] or "order" in tr["resolution"]["draft"].lower()

def test_policy_blocks_suspended():
    tr = run_ticket("refund $2500 now", "CUST-003")
    assert tr["status"] == "needs_approval"
    assert tr["resolution"]["action"]["approval_needed"] is True

def test_it_triage():
    tr = run_ticket("VPN timeout error 809", "CUST-001")
    assert tr["triage"]["category"] in ("it_network", "outage")
    assert tr["resolution"]["draft"]
