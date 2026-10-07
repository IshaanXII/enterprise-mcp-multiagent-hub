"""CLI demo for Loom — WHY: shows multi-agent comms + tool logs + error recovery in terminal."""
import json
from src.database import seed
from src.rag_store import ingest_chroma_if_available
from src.orchestrator import run_ticket

if __name__ == "__main__":
    print("== Seeding =="); print(seed()); print(ingest_chroma_if_available())
    cases = [
        ("Billing auto-refund (should AUTO-RESOLVE)", "Hi team, I was double charged $349 on ORD-1002 yesterday.\nPlease refund the duplicate urgently — payroll closes tomorrow.", "CUST-002"),
        ("IT VPN (should DRAFT with IT-002)", "Hello, VPN timeout error 809 since this morning on my laptop.\nNeed it for a client call in 2 hours, please help on priority.", "CUST-001"),
        ("Policy block (should NEEDS_APPROVAL — suspended + >$500)", "Invoice shows $2500 overcharge on ORD-1003 and delivery was late.\nRefund now — third billing error and account under review.", "CUST-003"),
        ("Password reset (IT-001)", "Locked out of Okta since last night and MFA codes not arriving.\nNeed password reset plus MFA re-enrolment before 10am shift.", "CUST-004"),
    ]
    for title, txt, cid in cases:
        print("\n" + "="*70 + f"\nCASE: {title}\nTicket: {txt} [{cid}]")
        tr = run_ticket(txt, cid)
        print(f"Triage: {tr['triage']} | RAG: {tr['rag_backend']} | Status: {tr['status']}")
        print("Draft:", tr["resolution"]["draft"])
        print("Action:", tr["resolution"]["action"])
        print("Tools:", json.dumps(tr["tools"], indent=2)[:800])
    print("\nFull JSON traces saved in logs/. Use these in Loom video.")
