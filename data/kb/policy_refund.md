# Refund & Billing Policy (FIN-001) — ENFORCED BY POLICY ENGINE

1. Auto-refund allowed ONLY if: amount <= $500 AND order delivered AND dispute count < 3 AND account status != 'suspended'.
2. Amount > $500 OR account suspended OR fraud flag -> status `needs_approval`, never auto-execute.
3. Duplicate charge: full refund + apology, cite order_id.
4. Partial delivery: pro-rata refund = (missing_qty / total_qty) * order_total.
5. All refunds must call `create_refund` tool and log ticket. Never invent refund IDs.

**RAG source:** Use for billing, refund, overcharge, duplicate charge, invoice tickets.
