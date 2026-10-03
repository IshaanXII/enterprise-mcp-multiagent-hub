# Demo Trace — paste this into report + use for Loom

## Case 1: Billing auto-refund (CUST-002, $349)
Input: "I was double charged $349 on ORD-1002, refund urgently"
- Triage: billing|P1|0.92 (rule, upgraded by 'urgently')
- MCP tools: get_customer -> active, get_orders -> ORD-1002 $349 delivered, get_disputes -> 1 open
- RAG (tfidf-fallback): policy_refund.md FIN-001 + fin_billing_dispute.md
- Policy: Eligible (<=500, active, <3 disputes) -> create_refund -> RFD-xxx
- Status: auto_resolved. Draft cites FIN-001 + order evidence.

## Case 2: VPN (CUST-001)
Input: "VPN timeout error 809, cannot connect"
- Triage: it_network|P2. RAG: it_vpn_runbook.md IT-002. Status: drafted.
- Draft: update client 5.2+, flush DNS, vpn-east->west.

## Case 3: Policy block (CUST-003, $2500, suspended)
Input: "Refund $2500 now!!!"
- Triage: billing|P2. CRM: suspended + fraud_flag=1 + 2 disputes.
- Policy: BLOCKED -> needs_approval, no create_refund call. This is your error-recovery + guardrail proof.

## Case 4: Password reset (CUST-004)
- Triage: it_access|P3. RAG: it_password_reset.md IT-001. Status: drafted.

## Tool log sample (from logs/trace_*.json -> tools[])
get_customer -> get_orders -> get_disputes -> retrieve(RAG) -> create_refund/log_ticket
Each trace shows triage.backend, rag_backend, resolution.backend (ollama vs template-fallback).
With Ollama running, backend=ollama; stopped -> template-fallback, same flow. Show both in Loom for Autonomy marks.
