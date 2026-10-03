"""RAG store — WHY RAG: grounds Resolution Agent in SOPs/policies, stops hallucination.
Backend auto: sentence-transformers + ChromaDB if installed, else sklearn TF-IDF (zero heavy deps).
This guarantees your 16GB demo works even before `pip install` of torch."""
from pathlib import Path
import json

KB_DIR = Path(__file__).resolve().parents[1] / "data" / "kb"
INDEX_PATH = Path(__file__).resolve().parents[1] / "data" / "rag_index.json"

def chunk(text: str, size=600, overlap=80):
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i+size])
        i += size - overlap
    return out

def load_chunks():
    docs = []
    for f in sorted(KB_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        for j, c in enumerate(chunk(text)):
            docs.append({"id": f"{f.stem}#{j}", "source": f.name, "text": c})
    return docs

# ---- TF-IDF fallback (always available) ----
_vectorizer = None
_matrix = None
_docs_cache = None

def _ensure_tfidf():
    global _vectorizer, _matrix, _docs_cache
    if _vectorizer is not None:
        return
    from sklearn.feature_extraction.text import TfidfVectorizer
    _docs_cache = load_chunks()
    _vectorizer = TfidfVectorizer(stop_words="english")
    _matrix = _vectorizer.fit_transform([d["text"] for d in _docs_cache])

def retrieve_tfidf(query: str, top_k=4):
    from sklearn.metrics.pairwise import cosine_similarity
    _ensure_tfidf()
    q = _vectorizer.transform([query])
    scores = cosine_similarity(q, _matrix)[0]
    idx = scores.argsort()[::-1][:top_k]
    return [{**_docs_cache[i], "score": float(scores[i])} for i in idx]

# ---- ChromaDB backend (used when deps present) ----
def retrieve_chroma(query: str, top_k=4):
    import chromadb
    from sentence_transformers import SentenceTransformer
    from pathlib import Path as P
    persist = str(P(__file__).resolve().parents[1] / "data" / "chroma_db")
    client = chromadb.PersistentClient(path=persist)
    col = client.get_or_create_collection("it_support_kb")
    if col.count() == 0:
        raise RuntimeError("chroma empty — run scripts/seed_and_ingest.py first")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    qe = model.encode([query]).tolist()
    res = col.query(query_embeddings=qe, n_results=top_k)
    out = []
    for i in range(len(res["ids"][0])):
        out.append({"id": res["ids"][0][i], "source": res["metadatas"][0][i].get("source", "?"),
                    "text": res["documents"][0][i], "score": 1 - res["distances"][0][i]})
    return out

def retrieve(query: str, top_k=4) -> tuple[list, str]:
    """Returns (docs, backend). Tries Chroma, falls back to TF-IDF."""
    try:
        docs = retrieve_chroma(query, top_k)
        return docs, "chroma+minilm"
    except Exception:
        return retrieve_tfidf(query, top_k), "tfidf-fallback"

def ingest_chroma_if_available() -> str:
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        docs = load_chunks()
        client = chromadb.PersistentClient(path=str(Path(__file__).resolve().parents[1] / "data" / "chroma_db"))
        # reset collection for idempotent seed
        try:
            client.delete_collection("it_support_kb")
        except Exception:
            pass
        col = client.create_collection("it_support_kb")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embs = model.encode([d["text"] for d in docs]).tolist()
        col.add(ids=[d["id"] for d in docs], documents=[d["text"] for d in docs],
                metadatas=[{"source": d["source"]} for d in docs], embeddings=embs)
        return f"chroma ingested {len(docs)} chunks"
    except Exception as e:
        # Always ensure TF-IDF index is warm
        _ensure_tfidf()
        INDEX_PATH.write_text(json.dumps({"docs": len(_docs_cache), "backend": "tfidf"}, indent=2))
        return f"chroma skipped ({e}); tfidf ready with {len(_docs_cache)} chunks"
