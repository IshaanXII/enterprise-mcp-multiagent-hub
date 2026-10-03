"""CLI demo for Loom — WHY: shows multi-agent comms + tool logs + error recovery in terminal."""
import json
from src.database import seed
from src.rag_store import ingest_chroma_if_available
from src.orchestrator import run_ticket

if __name__ == "__main__":
    print("== Seeding =="); print(seed()); print(ingest_chroma_if_available())
    cases = [
        ("Billing auto-refund (should AUTO-RESOLVE)", "I was double charged $349 on ORD-1002, refund urgently", "CUST-002"),
        ("IT VPN (should DRAFT with IT-002)", "VPN timeout error 809, cannot connect", "CUST-001"),
        ("Policy block (should NEEDS_APPROVAL — suspended + >$500)", "Refund $2500 now!!! overcharged", "CUST-003"),
        ("Password reset (IT-001)", "Locked out, need password reset, MFA not working", "CUST-004"),
    ]
    for title, txt, cid in cases:
        print("\n" + "="*70 + f"\nCASE: {title}\nTicket: {txt} [{cid}]")
        tr = run_ticket(txt, cid)
        print(f"Triage: {tr['triage']} | RAG: {tr['rag_backend']} | Status: {tr['status']}")
        print("Draft:", tr["resolution"]["draft"])
        print("Action:", tr["resolution"]["action"])
        print("Tools:", json.dumps(tr["tools"], indent=2)[:800])
    print("\nFull JSON traces saved in logs/. Use these in Loom video.")
