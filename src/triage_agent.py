"""Triage Agent — WHY: routes by intent+urgency so Resolution gets correct SOP + SLA.
Tries Ollama, else deterministic keyword rules (demo-safe)."""
import re
from src.llm_client import generate

CATEGORIES = ["billing", "it_access", "it_network", "outage", "general"]

def rule_triage(text: str) -> dict:
    t = text.lower()
    if any(k in t for k in ["outage", "down", "all users", "500 error", "breach"]):
        cat, pri = "outage", "P1"
    elif any(k in t for k in ["refund", "billing", "charged", "invoice", "overcharge", "duplicate"]):
        cat = "billing"
        pri = "P2" if any(k in t for k in ["urgent", "asap", "vip", "payroll", "failed"]) else "P3"
    elif any(k in t for k in ["vpn", "network", "wifi", "gateway", "zscaler", "tunnel"]):
        cat, pri = "it_network", "P2"
    elif any(k in t for k in ["password", "locked", "otp", "mfa", "login", "sso"]):
        cat, pri = "it_access", "P3"
    else:
        cat, pri = "general", "P4"
    if ("urgent" in t or "asap" in t or "!!!" in text) and pri != "P1":
        pri = "P" + str(max(1, int(pri[1]) - 1))  # upgrade one level
    conf = 0.92 if cat != "general" else 0.65
    return {"category": cat, "priority": pri, "confidence": conf, "backend": "rule"}

def triage(text: str) -> dict:
    prompt = f"""Classify ticket. Return ONLY: category|priority|confidence
Categories: {CATEGORIES}. Priority P1-P4 per SLA policy.
Ticket: {text}"""
    llm_text, backend = generate(prompt)
    if backend == "ollama" and "|" in llm_text:
        try:
            parts = [p.strip() for p in llm_text.split("|")]
            cat = parts[0].lower() if parts[0].lower() in CATEGORIES else "general"
            pri = parts[1].upper() if re.match(r"P[1-4]", parts[1].upper()) else "P3"
            conf = float(parts[2]) if len(parts) > 2 else 0.8
            return {"category": cat, "priority": pri, "confidence": conf, "backend": "ollama"}
        except Exception:
            pass
    r = rule_triage(text)
    # If Ollama gave garbage, still note attempt
    if backend == "ollama":
        r["backend"] = "ollama-fallback-to-rule"
    return r
