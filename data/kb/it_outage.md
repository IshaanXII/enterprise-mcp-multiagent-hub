# Outage & Escalation Runbook (IT-003)

1. If ticket text matches outage pattern OR 3 similar P1 in 1h, open incident `INC-<date>`.
2. Resolution Agent must NOT promise fix time; say "NetOps paged, update in 60 min".
3. Collect: region, service, start time, impact count.
4. Post to #incidents and assign to `oncall-netops`.

**RAG source:** Use for outage, down, 500 error, all users tickets.
