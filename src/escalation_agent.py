"""Escalation Agent — WHY: P1/outage + policy-blocks need human handoff with paging.
Rules-first (demo-safe), Ollama polishes the page message."""
from src.llm_client import generate

def escalate(ticket_id: str, triage: dict, customer: dict, resolution: dict) -> dict:
    needs = False
    reasons = []
    if triage.get("priority") == "P1" or triage.get("category") == "outage":
        needs = True; reasons.append("P1/outage — page on-call NetOps")
    if resolution.get("action", {}).get("approval_needed"):
        needs = True; reasons.append("Policy block (FIN-001) — human approval")
    if customer.get("tier") == "Enterprise" and triage.get("priority") in ("P1", "P2"):
        needs = True; reasons.append("Enterprise VIP — notify CSM")

    page = ""
    if needs:
        prompt = (f"Write 2-line escalation page for {ticket_id}: {'; '.join(reasons)}. "
                  f"Customer {customer.get('customer_id')} {customer.get('name')}. Ask for owner + 60-min update.")
        page, backend = generate(prompt)
        if not page or backend == "fallback":
            page = (f"ESCALATED {ticket_id}: {'; '.join(reasons)}. Owner: oncall-netops/CSM. "
                    f"Update in 60 min. SLA {triage.get('priority')}.")
            backend = "template-fallback"
    return {"escalated": needs, "reasons": reasons, "page": page,
            "queue": "oncall-netops" if triage.get("category") in ("outage", "it_network") else "csm-review"}
