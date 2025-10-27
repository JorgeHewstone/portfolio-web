FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0:8080
ENV OLLAMA_MODELS=/models
ENV OLLAMA_KEEP_ALIVE=5m

# Pre-descarga de modelos necesarios (embeddings + LLM)
# Nota: arrancamos 'ollama serve', esperamos, hacemos pull y matamos el proceso.
RUN (ollama serve & sleep 5) && \
    ollama pull nomic-embed-text:latest && \
    ollama pull qwen2.5:1.5b-instruct && \
    pkill ollama
