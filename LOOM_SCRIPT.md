# Loom 5-min script
0:00-0:40 — Show README + config.yaml + data/kb/ (6 docs). Say: "RAG grounds Resolution in FIN-001/SOPs, MCP is only DB access."
0:40-2:30 — Run `python scripts/run_demo.py`. Pause on 3 outputs: auto_resolved (refund ID), drafted VPN, needs_approval block for suspended. Point to Triage, RAG backend, Action lines.
2:30-3:40 — Open logs/trace_*.json. Highlight tools[], rag_docs[source,score], policy_reason. This covers 35% Tool Calling.
3:40-4:30 — Open http://localhost:8000/docs, POST /ticket live. Stop Ollama (or note fallback) to show error recovery — never crashes.
4:30-5:00 — `docker compose config` + `pytest -q` (3 passed). End with rubric mapping slide.
Tip: keep terminal font 14+, show file names clearly.
