// const host = window.location.hostname;
// const isLocal = host === "localhost" || host === "127.0.0.1" || host === "::1";

// const API_BASE = "https://portfolio-backend-joyc2o5k3a-tl.a.run.app"; // sin "/" al final

const host = window.location.hostname;
const isLocal = host === "localhost" || host === "127.0.0.1" || host === "::1";

const API_BASE = isLocal
  ? "http://127.0.0.1:8080"   // backend local
  : "https://portfolio-backend-101806568838.southamerica-west1.run.app"; // <-- tu backend prod


const proyectos = [
{
titulo: "Neural Network-Based Approach to Detect and Filter Misleading Audio Segments in Classroom Automatic Transcription",
img: "/assets/ciae.png",
desc: "Proyecto de investigación realizado con Phd Roberto Araya en la implementación de una red neuronal para detectar segmentos de audio que aumentaban las halucinaciones de un transcriptor.",
repo: "https://www.mdpi.com/2076-3417/13/24/13243"
},
{
titulo: "Podcast summarizer",
img: "/assets/podcast_summarizer.png",
desc: "Proyecto que genera resumenes técnicos a partir de videos/audios, diseñado para consultar podcasts especializados en finanzas.",
repo: "https://github.com/JorgeHewstone/Portfolio/tree/main/podcast_summarizer"
},
{
titulo: "SudokuApp",
img: "/assets/sudoku.jpg",
desc: "Aplicación personal creada para jugar Sudoku sin publicidad.",
repo: "https://github.com/JorgeHewstone/Portfolio/tree/main/SudokuApp"
},
{
titulo: "Portfolio con IA",
img: "/assets/sudoku.jpg",
desc: "Aplicación personal creada para jugar Sudoku sin publicidad.",
repo: "https://github.com/JorgeHewstone/Portfolio/tree/main/SudokuApp"
}
];


function el(tag, cls, text){ const e=document.createElement(tag); if(cls) e.className=cls; if(text) e.textContent=text; return e; }


function renderProyectos(){
const grid = document.getElementById('grid-proyectos');
proyectos.forEach(p => {
const card = el('div','card-proy');
const img = el('img'); img.src = p.img; img.alt = p.titulo;
const box = el('div','p');
const h3 = el('h3',null,p.titulo);
const d = el('p','muted',p.desc);
const a = el('a',null,'Ver repo →'); a.href=p.repo; a.target='_blank'; a.rel='noreferrer';
box.append(h3,d,a); card.append(img,box); grid.append(card);
});
}


function pushMsg(who, text){
const box = document.getElementById('chatbox');
const m = el('div', `msg ${who}`);
m.textContent = text; box.append(m); box.scrollTop = box.scrollHeight;
}


async function sendPrompt(q){
const r = await fetch(`${API_BASE}/chat`,{
method:'POST', headers:{'Content-Type':'application/json'},
body: JSON.stringify({ question:q })
});
if(!r.ok){ throw new Error(`HTTP ${r.status}`); }
const data = await r.json();
return data.answer;
}

async function sendPromptStream(q, { useRag = true, model = null } = {}, onChunk) {
  const res = await fetch(`${API_BASE}/chat_stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: q, use_rag: useRag, model })
  });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE simple: eventos separados por "\n\n" y líneas "data: ..."
    let idx;
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const event = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      if (event.startsWith('data: ')) {
        const chunk = event.slice(6);
        onChunk?.(chunk);
      }
    }
  }
}



function initChat(){
  const form  = document.getElementById('chat-form');
  const input = document.getElementById('user-input');
  const btn   = document.getElementById('send-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;

    pushMsg('user', q);
    input.value = '';
    btn.disabled = true;
    btn.textContent = '…';

    try {
      // Crea un bubble vacío que iremos llenando
      const box = document.getElementById('chatbox');
      const bubble = el('div', 'msg bot', '');
      box.append(bubble); box.scrollTop = box.scrollHeight;

      await sendPromptStream(
        q,
        { useRag: true, model: null }, // usa RAG del backend
        (chunk) => {
          bubble.textContent += chunk;
          box.scrollTop = box.scrollHeight;
        }
      );
    } catch (err) {
      pushMsg('bot', `Error: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Enviar';
    }
  }); // <<--- ESTE paréntesis y punto y coma faltaban
} // <<--- y este cierra initChat() correctamente


// EVALUAR EN EL FUTURO 
// async function sendPrompt(q){
//   const controller = new AbortController();
//   const t = setTimeout(() => controller.abort(), 15000); // 15s
//   try{
//     const r = await fetch(`${API_BASE}/chat`, {
//       method:'POST',
//       headers:{'Content-Type':'application/json'},
//       body: JSON.stringify({ question:q }),
//       signal: controller.signal
//     });
//     if (!r.ok) throw new Error(`HTTP ${r.status}`);
//     const data = await r.json();
//     return data.answer;
//   } finally {
//     clearTimeout(t);
//   }
// }


function welcome(sections){
  const nice = sections?.map(s =>
    s.replace(/^\d+_/, '').replace(/\..*$/, '').replace(/_/g, ' ')
  ).join(', ');
  const msg = [
    "¡Hola! Soy la versión virtual de Jorge \n",
    nice ? `Mi contexto se restringe a: ${nice}.` : null,
    "Pregúntame sobre mi formación, experiencia, cómo trabajo o mis proyectos."
  ].filter(Boolean).join(' ');
  pushMsg('bot', msg);
}

async function pingHealth(){
  try{
    const r = await fetch(`${API_BASE}/health`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    welcome(data.sections);
  }catch(err){
    pushMsg('bot', `No puedo conectar con el backend (${err.message}). Revisa API_BASE o Cloud Run.`);
    welcome(); // fallback sin secciones
  }
}

function main(){
  const y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  renderProyectos();
  initChat();
  pingHealth(); // dispara saludo + chequeo backend
}

document.addEventListener('DOMContentLoaded', main);

