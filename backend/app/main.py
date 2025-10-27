import os
import glob
from pathlib import Path
from typing import List, Tuple
import json
from fastapi.responses import StreamingResponse

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
# =========================
# RAG mínimo (embeddings + búsqueda coseno)
# =========================
EMBED_MODEL   = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
TOP_K         = int(os.getenv("TOP_K", "4"))

def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    out, start, L = [], 0, len(text)
    while start < L:
        end = min(start + size, L)
        out.append(text[start:end])
        if end == L:
            break
        start = max(0, end - overlap)
    return out

def _l2norm(vec: list[float]) -> float:
    s = 0.0
    for x in vec: s += x*x
    return (s ** 0.5) or 1.0

def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x*y for x, y in zip(a, b))  # asume L2=1

def _ollama_embed(texts: list[str]) -> list[list[float]]:
    """
    Embeddings via Ollama /api/embeddings
    """
    url = f"{OLLAMA_URL}/api/embeddings"
    headers = {"Content-Type": "application/json"}
    headers.update(_maybe_oidc_headers(OLLAMA_URL))
    payload = {"model": EMBED_MODEL, "input": texts if len(texts) > 1 else texts[0]}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        if "embeddings" in data: return data["embeddings"]
        if "embedding"  in data: return [data["embedding"]]
        raise HTTPException(status_code=502, detail="Embeddings: respuesta inesperada")
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Embeddings HTTP error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embeddings error: {e}")

class RagIndexItem(BaseModel):
    section: str
    chunk_id: int
    text: str
    vec: list[float]

RAG_INDEX: list[RagIndexItem] = []

def build_rag_index() -> None:
    """
    Lee SECTIONS -> chunking -> embeddings -> normaliza a L2=1 -> llena RAG_INDEX
    """
    global RAG_INDEX
    docs: list[tuple[str, int, str]] = []
    for name, txt in SECTIONS:
        for i, c in enumerate(_chunk_text(txt)):
            docs.append((name, i, c))
    if not docs:
        RAG_INDEX = []
        return
    texts = [c for _, _, c in docs]
    vecs  = _ollama_embed(texts)
    normed: list[RagIndexItem] = []
    for (name, i, c), v in zip(docs, vecs):
        n = _l2norm(v)
        v = [x / n for x in v]
        normed.append(RagIndexItem(section=name, chunk_id=i, text=c, vec=v))
    RAG_INDEX = normed

def _rag_search(query: str, k: int = TOP_K) -> list[RagIndexItem]:
    if not RAG_INDEX:
        return []
    qv  = _ollama_embed([query])[0]
    n   = _l2norm(qv)
    qv  = [x / n for x in qv]
    scored = [( _cosine(qv, it.vec), it ) for it in RAG_INDEX]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [it for _, it in scored[:k]]

def build_rag_system_prompt(query: str, hits: list[RagIndexItem]) -> str:
    refs = "\n\n".join([f"### {h.section} [chunk {h.chunk_id}]\n{h.text}" for h in hits])
    return (
        f"{SYSTEM_PREFIX}\n\n"
        f"Responde únicamente con base en los fragmentos relevantes. "
        f"Si no está en los textos, dilo claro.\n\n"
        f"Consulta: {query}\n\n"
        f"Fragmentos relevantes:\n{refs}"
    )

# =========================
# Config básica
# =========================
APP_DIR = Path(__file__).resolve().parent
CONTEXT_DIR = APP_DIR / "context"

# URL del servicio de Ollama
# - Local dev:  OLLAMA_URL=http://localhost:11434
# - Cloud Run:  OLLAMA_URL=https://<ollama-svc-xyz-uc.a.run.app>
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

# Modelo por defecto a usar en Ollama
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:1.5b-instruct")

# =========================
# Carga de contexto (TXT) — NO HAY RETRIEVAL
# =========================
def load_sections() -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    for path in sorted(glob.glob(str(CONTEXT_DIR / "*.txt"))):
        name = Path(path).name
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read().strip()
        if txt:
            sections.append((name, txt))
    return sections

SECTIONS = load_sections()  # cache en memoria

SYSTEM_PREFIX = (
    """Eres la representación virtual de Jorge Hewstone Correa, 
    un ingeniero matemático con magister en ciencias de datos experto en inteligencia artificial. 
    Tendrás acceso a la información de Jorge para poder responder las preguntas con precisión (no inventes nada concreto).
    Instrucciones: 
    Sé breve, directo y profesional.
    Tus respuestas deben ser conscisas y profesionales, ninguna respuesta debe tener más de 150 palabras. Si te 
    preguntan por algo que puede ser largo desarrollalo en pasos y pregunta al usuario si seguir por ejemplo:
    Usuario: 'Dime de que manera tú (Jorge) desarrollaría desde cero un modelo de ML para predecir la probabilidad de que un 
              cliente caiga en default (incumplimiento de pago) en un crédito de consumo durante los próximos 12 meses'
    Respuesta: 'Que buen proyecto. Como ingenierio especializado en IA y con experiencia en varias metodologías de proyectos 
                creo que lo que seguramente haría sería estructurarlo en 6 etapas claras ¿Quieres que te las explique?'
    Usuario: 'Sí por favor, sigue'
    Respuesta: 'Bueno, en primer lugar, lo que haría sería comprender el objetivo de negocio. 
                Antes que nada, debo saber para qué se usará el modelo: 
                ¿es para aprobación automática o para asistir a un analista? 
                Lo más importante es definir el costo de los errores: 
                ¿qué es peor, un Falso Positivo (prestar a quien no pagará) o un Falso Negativo (negar a quien sí pagaría)? 
                De esto depende la métrica de éxito. ¿Sigo con el siguiente paso?'
    Usuario: 'Sigue por favor'
    Respuesta: 'Luego de tener eso claro, 
                seguiría con la exploración y recolección de datos (EDA). 
                Aquí me pregunto: ¿qué datos tenemos? Analizaría el historial transaccional, demográfico y crediticio de los clientes. 
                Mi foco sería la calidad del dato: 
                buscaría valores nulos, outliers 
                y entendería las distribuciones de las variables para limpiarlas y prepararlas.
                ¿Sigo con el siguiente paso?'
    Usuario: 'Puedes decirme todos los pasos de una sola vez?'
    Respuesta: 'Sí claro:
                Paso 1: Comprender objetivo de negocio ¿Qué métrica mide el éxito?'
                Paso 2: Exploración y recolección de datos. ¿Cuál es la calidad, cantidad e importancia de los datos que tenemos?
                Paso 3: Feature Engineering, definir labels y features de acuerdo a la naturaleza del problema. Hay posibles leakages?
                Paso 4: Modelamiento, comenzaría con un modelo simple de regresión logística que sea interpretable, luego probaría modelos
                        más complejos como XGBoost o Random Forest.
                Paso 5: Evaluación, considerando el paso número 1 buscaría las mejores métricas y evitaría sesgos. 
                Paso 6: Despliegue y monitoreo; Dependiendo del esquema de gastos de la empresa y el caso de uso
                        usaría una api o un servicio de nube para pasarlo a producción. Implementaría un sistema de MLOps para monitorear el
                        envejecimiento del modelo.'

    """
)
# Construir índice RAG al iniciar
try:
    build_rag_index()
    RAG_READY = True
except Exception:
    RAG_READY = False

def build_system_prompt() -> str:
    """Concatena TODO el contexto sin búsqueda."""
    if not SECTIONS:
        return SYSTEM_PREFIX
    joined = "\n\n".join([f"### {name}\n{txt}" for name, txt in SECTIONS])
    return f"{SYSTEM_PREFIX}\n\nTextos de referencia:\n{joined}"

# =========================
# App FastAPI + CORS
# =========================
app = FastAPI(title="JHC Chatbot", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # afinar en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Modelos de entrada/salida
# =========================
class ChatIn(BaseModel):
    question: str
    model: str | None = None  # opcional, usa env por defecto

# =========================
# Utilidades: invocar Ollama /api/chat
# =========================
def _maybe_oidc_headers(audience: str) -> dict:
    """
    Si OLLAMA_URL es https (Cloud Run privado), agrega ID token OIDC.
    Si es http (local), no agrega nada.
    """
    if OLLAMA_URL.startswith("https://"):
        try:
            from google.auth.transport.requests import Request as GoogleRequest
            from google.oauth2 import id_token
            tok = id_token.fetch_id_token(GoogleRequest(), audience)
            return {"Authorization": f"Bearer {tok}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OIDC error: {e}")
    return {}


def _ollama_chat(prompt_system: str, user_question: str, model_name: str) -> str:
    """
    Llama a Ollama /api/chat con mensajes [system, user] y devuelve el texto.
    """
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": model_name,
        "stream": False,
        "messages": [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": f"Pregunta del usuario: {user_question}\nResponde en español en 3–6 líneas."}
        ],
        # Opciones que aceleran sin perder demasiado:
        "options": {
            "num_ctx": 2048,         # suficiente para tu contexto
            "num_predict": 200,      # corta respuestas (más rápido)
            "temperature": 0.3,
            # "num_thread": 4,       # puedes fijarlo si tu CPU es 4c; si no, omitelo
        }
    }
    headers = {"Content-Type": "application/json"}
    headers.update(_maybe_oidc_headers(OLLAMA_URL))

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=120)
        r.raise_for_status()
        data = r.json()
        # Formato típico de Ollama /api/chat:
        # { "model": "...", "message": {"role":"assistant","content":"..."}, ... }
        msg = (data.get("message") or {}).get("content")
        if not msg:
            # Algunos builds devuelven lista de 'messages' o 'done' con 'response'
            msg = data.get("response") or ""
        return msg.strip() if msg else "[Sin respuesta del modelo]"
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Ollama HTTP error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

def _ollama_chat_stream(prompt_system: str, user_question: str, model_name: str):
    """
    Llama a Ollama /api/chat con stream=True y emite Server-Sent Events (SSE).
    """
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": model_name,
        "stream": True,
        "messages": [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": f"Pregunta del usuario: {user_question}\nResponde en español en 3–6 líneas."}
        ],
        "options": {
            "num_ctx": 2048,
            "num_predict": 160,
            "temperature": 0.3,
        }
    }
    headers = {"Content-Type": "application/json"}
    headers.update(_maybe_oidc_headers(OLLAMA_URL))

    with requests.post(url, json=payload, headers=headers, stream=True) as r:
        r.raise_for_status()
        for raw in r.iter_lines():
            if not raw:
                continue
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception:
                continue

            # Ollama envía fragmentos JSON; tomamos el texto incremental
            chunk = ((obj.get("message") or {}).get("content")) or obj.get("response") or ""
            if chunk:
                # Formato SSE
                yield f"data: {chunk}\n\n"

            if obj.get("done"):
                break

        # Señal de cierre opcional
        yield "event: done\ndata: [DONE]\n\n"

# =========================
# Endpoints
# =========================
@app.get("/health")
async def health():
    return {
        "ok": True,
        "sections": [name for name, _ in SECTIONS],
        "model": MODEL_NAME,
        "ollama_url": OLLAMA_URL,
        "rag": {
            "ready": RAG_READY,
            "chunks": len(RAG_INDEX),
            "embed_model": EMBED_MODEL,
        }
    }


@app.post("/chat")
async def chat(q: ChatIn):
    question = (q.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question vacío")
    system_prompt = build_system_prompt()
    model_name = (q.model or MODEL_NAME)
    answer = _ollama_chat(system_prompt, question, model_name)
    return {"answer": answer, "model": model_name}


class ChatRagIn(BaseModel):
    question: str
    model: str | None = None
    top_k: int | None = None

@app.post("/chat_rag")
async def chat_rag(q: ChatRagIn):
    question = (q.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question vacío")
    if not RAG_INDEX:
        raise HTTPException(status_code=500, detail="RAG no está listo (índice vacío)")

    k = q.top_k or TOP_K
    hits = _rag_search(question, k=k)
    sys_prompt = build_rag_system_prompt(question, hits)
    model_name = (q.model or MODEL_NAME)
    answer = _ollama_chat(sys_prompt, question, model_name)
    return {
        "answer": answer,
        "model": model_name,
        "top_k": k,
        "hits": [{"section": h.section, "chunk_id": h.chunk_id} for h in hits],
    }

@app.post("/rag/rebuild")
async def rag_rebuild():
    try:
        global SECTIONS, RAG_READY
        SECTIONS = load_sections()
        build_rag_index()
        RAG_READY = True
        return {"ok": True, "chunks": len(RAG_INDEX)}
    except Exception as e:
        RAG_READY = False
        raise HTTPException(status_code=500, detail=f"RAG rebuild error: {e}")

import time

@app.post("/bench")
async def bench(q: ChatIn):
    question = q.question.strip() if q.question else "Dame un resumen de mi experiencia."
    system_prompt = build_system_prompt()
    model_name = (q.model or MODEL_NAME)
    t0 = time.perf_counter()
    answer = _ollama_chat(system_prompt, question, model_name)
    dt = time.perf_counter() - t0
    return {"model": model_name, "latency_sec": round(dt, 3), "chars": len(answer), "answer": answer[:200]}

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


class ChatStreamIn(BaseModel):
    question: str
    model: str | None = None
    use_rag: bool | None = True
    top_k: int | None = None

@app.post("/chat_stream")
async def chat_stream(q: ChatStreamIn):
    question = (q.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question vacío")

    model_name = (q.model or MODEL_NAME)

    if q.use_rag:
        if not RAG_INDEX:
            raise HTTPException(status_code=500, detail="RAG no está listo (índice vacío)")
        k = q.top_k or TOP_K
        hits = _rag_search(question, k=k)
        sys_prompt = build_rag_system_prompt(question, hits)
    else:
        sys_prompt = build_system_prompt()

    gen = _ollama_chat_stream(sys_prompt, question, model_name)
    return StreamingResponse(gen, media_type="text/event-stream")
