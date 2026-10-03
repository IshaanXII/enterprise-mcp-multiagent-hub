FROM python:3.12-slim

WORKDIR /app

# System deps for chroma + sklearn
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

# Seed DB + ingest KB on first start (idempotent)
RUN PYTHONPATH=/app python scripts/seed_and_ingest.py || true

EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
