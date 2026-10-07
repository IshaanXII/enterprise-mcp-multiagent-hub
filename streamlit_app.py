"""Streamlit Cloud app — WHY separate from FastAPI: Streamlit Cloud can't run
Ollama (4.9GB), Docker, or Chroma build tools. This uses same orchestrator in
fallback/template + TF-IDF mode, so public URL demo always works.
Local full power stays in src/api.py + Ollama."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from src.database import seed
from src.rag_store import ingest_chroma_if_available
from src.orchestrator import run_ticket
from src.analytics_agent import overview as analytics_overview

st.set_page_config(page_title="Enterprise MCP IT Hub + RAG", layout="wide")
st.title("Enterprise MCP IT & Customer Service Hub + RAG")
st.caption("Multi-agent: Triage → CRM-MCP → RAG → Resolution → Escalation + Analytics. Cloud = resilient mode; local/Docker = Ollama + Chroma.")

@st.cache_resource
def _init():
    seed()
    return ingest_chroma_if_available()

rag_status = _init()
st.sidebar.info(f"RAG init: {rag_status}")
st.sidebar.markdown("**Sample customers:** CUST-001 Aarav (VPN) · CUST-002 Diya ($349 refund) · CUST-003 Kabir (suspended, blocked) · CUST-004 Meera (password)")

@st.cache_data
def _customers():
    import sqlite3
    from src.database import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("SELECT customer_id FROM customers ORDER BY customer_id").fetchall()
    conn.close()
    ids = [r[0] for r in rows] or ["CUST-002", "CUST-001", "CUST-003", "CUST-004"]
    demo = ["CUST-002", "CUST-001", "CUST-003", "CUST-004"]
    return demo + [c for c in ids if c not in demo]

SAMPLES = {
    "CUST-002": "Hi team, I was double charged $349 on order ORD-1002 yesterday.\nPlease refund the duplicate urgently — payroll closes tomorrow and I need it reversed.",
    "CUST-001": "Hello, VPN timeout error 809 since this morning on my laptop.\nI updated nothing; need it for a client call in 2 hours, please help on priority.",
    "CUST-003": "Your invoice shows $2500 overcharge on ORD-1003 and delivery was late.\nRefund the full amount now — this is the third billing error and my account is already under review.",
    "CUST-004": "Hi, I am locked out of Okta since last night and MFA codes are not arriving.\nNeed a password reset plus MFA re-enrolment before my 10am shift starts.",
}
def _default_sample(cid: str) -> str:
    return (f"Hello support team, this is {cid}. I need help with my recent order.\n"
            f"Please check account {cid} and advise next steps with expected timeline.")

col1, col2 = st.columns([1, 2])
with col1:
    all_customers = _customers()
    st.caption(f"{len(all_customers)} customers loaded (type to search)")
    customer_id = st.selectbox("Customer (search any of 500)", all_customers)
    if "last_cust" not in st.session_state or st.session_state.last_cust != customer_id:
        st.session_state.ticket_text = SAMPLES.get(customer_id, _default_sample(customer_id))
        st.session_state.last_cust = customer_id
    text = st.text_area("Ticket text (auto-filled per customer, editable)", key="ticket_text", height=120)
    run = st.button("Run pipeline", type="primary")
    st.markdown("Samples auto-fill when you change customer. Your screenshot mismatch (CUST-004 + $349 text) happened because text was typed manually.")

if run:
    with st.spinner("Running Triage → MCP CRM → RAG → Resolution → Escalation…"):
        tr = run_ticket(text, customer_id)
    st.session_state.last_trace = tr
    st.session_state.decision = None
tr = st.session_state.get("last_trace")
if tr:
    with col2:
        st.subheader(f"Status: {tr['status']}" + (f" → {st.session_state.decision}" if st.session_state.get("decision") else ""))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Category", tr["triage"]["category"])
        c2.metric("Priority", tr["triage"]["priority"])
        c3.metric("RAG", tr.get("rag_backend", "?"))
        esc = tr.get("escalation", {})
        c4.metric("Escalated", "Yes" if esc.get("escalated") else "No")
        st.markdown("**Resolution draft**")
        st.write(tr["resolution"]["draft"])
        if tr["resolution"]["action"].get("type") == "auto_refund":
            st.success(f"Refund initiated for order {tr['resolution']['action']['refund']['order_id']} — 3-5 days.")
        # 5. Human-in-the-loop approval for policy blocks
        if tr["status"] == "needs_approval" and not st.session_state.get("decision"):
            st.warning("Our policy needs a quick human check before refund. Staff: approve or reject below.")
            b1, b2 = st.columns(2)
            if b1.button("Approve refund", type="primary"):
                from src import mcp_client as _mc
                ords = tr["crm"].get("orders", [])
                if ords:
                    rf = _mc.call("create_refund", order_id=ords[0]["order_id"], amount=float(ords[0]["amount"]))
                    st.session_state.decision = f"APPROVED → {rf['refund_id']} (${rf['amount']})"
                else:
                    st.session_state.decision = "APPROVED (no order found — manual review)"
                st.rerun()
            if b2.button("Reject"):
                st.session_state.decision = "REJECTED → ticket closed, customer notified"
                st.rerun()
        with st.expander("Staff view — evidence, citations, tools (for evaluator)"):
            st.markdown("**Action detail**")
            st.json(tr["resolution"]["action"])
            st.markdown("**RAG citations (click to verify grounding)**")
            for i, doc in enumerate(tr.get("rag_docs", [])):
                with st.expander(f"[{i+1}] {doc.get('source')} — score {doc.get('score')}"):
                    st.write(doc.get("excerpt", "(no text)"))
            st.markdown("**Escalation (Supervisor agent)**")
            st.json(tr.get("escalation", {}))
            st.markdown("**CRM context**")
            st.json(tr["crm"])
            st.markdown("**Tool calls (MCP)**")
            st.json(tr.get("tools", []))
else:
    with col2:
        st.info("Pick a sample on the left and press Run pipeline. For evaluation: CUST-002 auto-resolves, CUST-003 needs_approval (policy block).")

st.divider()
with st.expander("Manager view — Analytics Agent (SLA risk, refunds, workload)", expanded=False):
    st.caption("Internal only: customers don't need ticket counts or refund totals.")
    try:
        a = analytics_overview()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tickets", a["tickets_total"])
        m2.metric("Refunds total $", a["refunds_total"])
        m3.metric("At-risk (P1/needs_approval)", a["at_risk_count"])
        auto = a["by_status"].get("auto_resolved", 0)
        m4.metric("Auto-resolved", auto)
        st.json(a)
    except Exception as e:
        st.warning(f"Analytics unavailable: {e}")
