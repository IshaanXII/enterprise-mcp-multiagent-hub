"""FastAPI — WHY: gives evaluators a 1-click UI + JSON trace for Loom video."""
from fastapi import FastAPI
from pydantic import BaseModel
from src.orchestrator import run_ticket
from src.database import seed
from src.rag_store import ingest_chroma_if_available
from src.analytics_agent import overview as analytics_overview

app = FastAPI(title="Enterprise MCP IT & Customer Service Hub + RAG")

class TicketIn(BaseModel):
    text: str
    customer_id: str = "CUST-002"

@app.on_event("startup")
def _startup():
    seed()
    ingest_chroma_if_available()

@app.get("/")
def home():
    return {"msg": "POST /ticket with {text, customer_id}. GET /demo runs 3 sample tickets.", "docs": "/docs"}

@app.post("/ticket")
def handle(t: TicketIn):
    return run_ticket(t.text, t.customer_id)

@app.get("/demo")
def demo():
    samples = [
        ("I was double charged $349, please refund urgently", "CUST-002"),
        ("VPN timeout error 809, cannot connect since morning", "CUST-001"),
        ("CUST-003 overcharge $2500 — refund now!!!", "CUST-003"),
    ]
    return [run_ticket(txt, cid) for txt, cid in samples]

@app.get("/analytics")
def analytics():
    return analytics_overview()
