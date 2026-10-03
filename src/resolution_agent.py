"""Resolution Agent — WHY: drafts grounded answer + enforces FIN-001 refund guardrails.
Flow: CRM context + RAG docs + policy check -> Ollama draft (or template) -> action."""
import re
import yaml
from pathlib import Path
from src.llm_client import generate

CFG = yaml.safe_load(open(Path(__file__).resolve().parents[1] / "config.yaml"))
AUTO_MAX = CFG["policy"]["auto_refund_max"]

def policy_check(customer: dict, order: dict | None, amount: float) -> tuple[bool, str]:
    if customer.get("status") == "suspended" or customer.get("fraud_flag"):
        return False, "Account suspended / fraud flag — needs human approval (FIN-001)."
    if amount > AUTO_MAX:
        return False, f"Amount ${amount} > auto-limit ${AUTO_MAX} — needs approval (FIN-001)."
    disputes = customer.get("_disputes", [])
    if len(disputes) >= 3:
        return False, "Dispute count >=3 — fraud review required."
    return True, "Eligible for auto-refund."

def resolve(ticket_text: str, triage: dict, customer: dict, orders: list, disputes: list, rag_docs: list) -> dict:
    customer["_disputes"] = disputes
    ctx_orders = "; ".join([f"{o['order_id']} ${o['amount']} {o['status']}" for o in orders]) or "none"
    rag_txt = "\n".join([f"[{d['source']}] {d['text'][:400]}" for d in rag_docs])
    categories_needing_refund = triage["category"] == "billing"

    order = orders[0] if orders else None
    amount = order["amount"] if order else 0.0
    allowed, reason = policy_check(customer, order, amount) if categories_needing_refund and order else (False, "No billing action needed.")

    prompt = f"""You are Resolution Agent. Use ONLY context below. Cite policy IDs.
Ticket: {ticket_text}
Triage: {triage}
Customer: {customer}
Orders: {ctx_orders}
RAG: {rag_txt}
Policy check: {reason}
Write 4-line response: acknowledge, evidence (order/customer), policy citation, action+SLA. If billing and allowed=False say 'needs_approval'.
STRICT: NEVER invent refund IDs like RFD-xxx. Do NOT write any Refund ID — it comes from create_refund tool after you."""
    draft, backend = generate(prompt)
    # Strip any hallucinated refund IDs — real ID is injected by orchestrator from create_refund tool
    if draft:
        draft = re.sub(r"Refund ID:\s*RFD-[A-Z0-9]+", "Refund will be initiated (ID from system)", draft)
        draft = re.sub(r"\bRFD-[A-Z0-9]{3,}\b", "[system-refund-id]", draft)

    action = {"type": "draft_reply", "refund": None, "approval_needed": False}
    if categories_needing_refund and order:
        if allowed:
            action = {"type": "auto_refund", "refund": {"order_id": order["order_id"], "amount": amount}, "approval_needed": False}
        else:
            action = {"type": "draft_reply", "refund": None, "approval_needed": True, "reason": reason}

    if not draft or backend == "fallback":
        # Deterministic template — guarantees demo quality without LLM
        if triage["category"] == "billing" and order:
            draft = (f"We found order {order['order_id']} (${amount}, {order['status']}) for {customer.get('name')}. "
                     f"Per FIN-001: {reason} " + (f"Refund will be initiated, 3-5 days. SLA {triage['priority']}." if allowed else "Escalated for approval. SLA " + triage["priority"] + "."))
        elif triage["category"] == "it_access":
            draft = ("Per IT-001: identity verified, account unlock + Okta reset (24h temp password, MFA re-enrol). " f"SLA {triage['priority']}.")
        elif triage["category"] == "it_network":
            draft = ("Per IT-002: update VPN client to 5.2+, flush DNS, switch vpn-east->vpn-west. If 3+ similar, P1 outage. " f"SLA {triage['priority']}.")
        elif triage["category"] == "outage":
            draft = ("Per IT-003/OPS-001 P1: NetOps paged, incident opened, update in 60 min. Share region/service/start-time. " f"SLA {triage['priority']}.")
        else:
            draft = (f"Acknowledged ({triage['category']}, {triage['priority']}). Checked CRM + KB. Next step assigned. SLA {triage['priority']}.")
        backend = "template-fallback" if backend == "fallback" else backend

    return {"draft": draft, "action": action, "policy_reason": reason, "backend": backend}
