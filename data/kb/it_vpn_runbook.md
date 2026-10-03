# VPN Connectivity Runbook (IT-002)

**Symptoms:** VPN timeout, error 809/789, split-tunnel DNS failure.

**Diagnosis:**
1. Check outage flag: if 3+ VPN tickets in 30 min -> declare P1 outage.
2. Ask user: OS, client version, network (home/office), error code.
3. Steps: update client to 5.2+, flush DNS, switch gateway from `vpn-east` to `vpn-west`.
4. If still failing, collect logs and escalate to NetOps queue.

**SLA:** P2 default, P1 if outage.
**RAG source:** Use for VPN, Zscaler, gateway, tunnel tickets.
