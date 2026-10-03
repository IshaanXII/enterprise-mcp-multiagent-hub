# Billing Dispute Handling (FIN-002)

1. Always fetch `get_customer`, `get_orders`, `get_disputes` before drafting.
2. If past disputes >= 2, add fraud-review note, do not auto-refund.
3. Response template: acknowledge -> state order_id + amount -> cite policy FIN-001 -> propose action -> SLA.
4. Tone: professional, concise, no blame.

Example: "We found order ORD-1002 ($349) duplicate-charged. Per FIN-001 you qualify for auto-refund. Refund RFD-xxx initiated, 3-5 days."
