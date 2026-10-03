"""Ollama client with deterministic fallback — WHY: your laptop is 16GB and Ollama
is not installed yet, so demo must never crash. Tries Ollama first, else rules."""
import os
import requests

MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def ollama_available() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def generate(prompt: str, system: str = "You are an enterprise IT support agent. Be concise, grounded, cite policy IDs.") -> tuple[str, str]:
    """Returns (text, backend) where backend is 'ollama' or 'fallback'."""
    if ollama_available():
        try:
            r = requests.post(
                f"{BASE_URL}/api/generate",
                json={"model": MODEL, "prompt": prompt, "system": system,
                      "stream": False, "options": {"temperature": 0.2}},
                timeout=60,
            )
            r.raise_for_status()
            return r.json().get("response", "").strip(), "ollama"
        except Exception as e:
            return f"[Ollama error, using fallback: {e}]", "fallback"
    return "", "fallback"
