# SLA Policy (OPS-001)

- P1 Critical (outage, security breach, data loss): 4h, page on-call, notify leadership.
- P2 High (VIP blocked, payment failure): 8h.
- P3 Medium (password reset, single-user bug): 24h.
- P4 Low (how-to, feature request): 72h.

**Triage rules:**
- Keywords `down, outage, breach, data loss, all users` -> P1.
- `payment failed, vip, ceo, payroll` -> P2.
- `password, locked, how to` -> P3/P4.
- Sentiment + caps + `urgent/asap` upgrades by 1 level (max P1).

**RAG source:** Use to justify priority in every resolution.
