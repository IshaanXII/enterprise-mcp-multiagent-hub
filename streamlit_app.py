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

SAMPLES = {
    "CUST-002": "I was double charged $349, please refund urgently",
    "CUST-001": "VPN timeout error 809, cannot connect since morning",
    "CUST-003": "Refund $2500 now, overcharged!!!",
    "CUST-004": "Locked out, need password reset, MFA not working",
}

col1, col2 = st.columns([1, 2])
with col1:
    customer_id = st.selectbox("Customer", ["CUST-002", "CUST-001", "CUST-003", "CUST-004"])
    if "last_cust" not in st.session_state or st.session_state.last_cust != customer_id:
        st.session_state.ticket_text = SAMPLES[customer_id]
        st.session_state.last_cust = customer_id
    text = st.text_area("Ticket text (auto-filled per customer, editable)", key="ticket_text", height=120)
    run = st.button("Run pipeline", type="primary")
    st.markdown("Samples auto-fill when you change customer. Your screenshot mismatch (CUST-004 + $349 text) happened because text was typed manually.")

if run:
    with st.spinner("Running Triage → MCP CRM → RAG → Resolution → Escalation…"):
        tr = run_ticket(text, customer_id)
    with col2:
        st.subheader(f"Status: {tr['status']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Category", tr["triage"]["category"])
        c2.metric("Priority", tr["triage"]["priority"])
        c3.metric("RAG", tr.get("rag_backend", "?"))
        esc = tr.get("escalation", {})
        c4.metric("Escalated", "Yes" if esc.get("escalated") else "No")
        st.markdown("**Resolution draft**")
        st.write(tr["resolution"]["draft"])
        st.markdown("**Action**")
        st.json(tr["resolution"]["action"])
        st.markdown("**Escalation (Supervisor agent)**")
        st.json(tr.get("escalation", {}))
        st.markdown("**CRM context**")
        st.json(tr["crm"])
        st.markdown("**RAG sources**")
        st.json(tr.get("rag_docs", []))
        st.markdown("**Tool calls (MCP)**")
        st.json(tr.get("tools", []))
else:
    with col2:
        st.info("Pick a sample on the left and press Run pipeline. For evaluation: CUST-002 auto-resolves, CUST-003 needs_approval (policy block).")

st.divider()
st.subheader("Analytics Agent — SLA risk, refunds, workload")
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
