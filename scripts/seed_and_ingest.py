"""Seed DB + ingest KB — WHY idempotent: safe to run in Docker build + locally."""
from src.database import seed
from src.rag_store import ingest_chroma_if_available

if __name__ == "__main__":
    print("DB:", seed())
    print("RAG:", ingest_chroma_if_available())
