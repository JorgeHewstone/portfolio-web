FROM python:3.11-slim

WORKDIR /app

# ====== Sistema base ======
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# ====== Dependencias Python ======
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ====== Código ======
COPY app ./app

# ====== Config por defecto (puedes sobreescribir con -e en runtime) ======
ENV PORT=8080
# El ganador de tus benchmarks:
ENV MODEL_NAME=qwen2.5:1.5b-instruct
# Embeddings para RAG:
ENV EMBED_MODEL=nomic-embed-text
# Chunking para RAG:
ENV CHUNK_SIZE=900
ENV CHUNK_OVERLAP=120
ENV TOP_K=4
# IMPORTANTE: en Compose/Cloud Run apunta a http://ollama:11434 o a la URL HTTPS de Cloud Run
ENV OLLAMA_URL=http://ollama:11434

# ====== Arranque ======
EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
