# Portafolio de Jorge Hewstone — ML Engineer

> Sitio web personal con proyectos, blog y chat, desplegado en Firebase Hosting.

[![Hecho con - HTML/CSS/JS](https://img.shields.io/badge/hecho%20con-HTML%2FCSS%2FJS-informational)](#)
[![Firebase Hosting](https://img.shields.io/badge/deploy-Firebase%20Hosting-orange)](#)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green)](#license)

## ✨ Características

* **Presentación**: carta de presentación y foto profesional.
* **Proyectos**: listado de proyectos con enlaces, descripciones y tags (ML, MLOps, SQL, GCP).
* **Chat**: sección de interacción sencilla.
* **Diseño**: layout limpio, tema oscuro y estilos responsivos.
* **Despliegue**: integración con Firebase Hosting y dominio propio.

## 🧱 Stack

* **Frontend**: HTML5, CSS3, JavaScript (vanilla)
* **Infraestructura**: Firebase Hosting
* **Integración**: API backend configurable vía `API_BASE`

## 📁 Estructura del proyecto

```
root/
├─ assets/           # imágenes, íconos, etc.
├─ styles.css        # estilos principales
├─ app.js            # lógica del sitio (fetch a API, interacciones)
├─ index.html        # página principal
├─ firebase.json     # configuración de Hosting
└─ .firebaserc       # alias de proyecto de Firebase
```

## ⚙️ Configuración

1. **Clonar el repo**

   ```bash
   git clone https://github.com/<usuario>/<repo>.git
   cd <repo>
   ```
2. **Instalar CLI de Firebase (opcional para deploy)**

   ```bash
   npm i -g firebase-tools
   firebase login
   firebase use <ID_DEL_PROYECTO>
   ```
3. **Configurar base de API (si usas backend)**
   En `app.js` se detecta entorno local vs producción y se define `API_BASE`.

   ```js
   const host = window.location.hostname;
   const isLocal = host === "localhost" || host === "127.0.0.1" || host === "::1";
   const API_BASE = isLocal ? "http://127.0.0.1:8080" : "https://tu-dominio-o-endpoint";
   ```

---

## 🔒 Seguridad y qué **no** va en el repo

Para publicar este proyecto sin exponer nada sensible, **se omiten** del repositorio los siguientes elementos. Si los necesitas, crea los *placeholders* indicados y configura los valores reales como **variables de entorno** o **secrets** del proveedor (GitHub/GCP/etc.).

**Omitidos por seguridad/privacidad**

* `*.env`, `.env.*`, `*.local` → variables de entorno (p. ej. `OLLAMA_URL`, `MODEL_NAME`, `EMBED_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `API_KEY`).
* `**/*serviceAccount*.json`, claves `*.pem`/`*.key`, credenciales de GCP/Firebase.
* `firebase-debug.log`, `.firebase/`, `.firebaserc.local`.
* Archivos de **contexto privado**: `context/*.txt` con datos personales o internos.
* Datos brutos pesados o sensibles en `assets/` (sube versiones anonimizadas o de muestra).

**Por qué se omiten**

* Evitar exposición de credenciales y endpoints internos.
* Mantener confidencial la información del contexto (si contiene datos privados).
* Reducir tamaño e historial del repo.

**Qué debería ir ahí (en general)**

* Un `.env.example` con los **nombres** de variables (sin valores).
* Un `context/README.md` describiendo qué textos colocar y su formato.
* Reglas de `CORS` y `Rules` documentadas en el README (no el archivo real de credenciales).

**.gitignore mínimo**

```gitignore
# Entornos/credenciales
.env
.env.*
*.local
**/*serviceAccount*.json
**/*.pem
**/*.key

# Firebase / logs
.firebase/
.firebaserc.local
firebase-debug.log
storage-debug.log

# Node / tooling
node_modules/
dist/
build/
.tmp/
.cache/
.eslintcache

# IDE/OS
.vscode/
.DS_Store
Thumbs.db
```

**Si subiste algo sensible por error**

1. elimina del repo y haz commit (`git rm --cached archivo`), 2) **rota** esa credencial en el proveedor. (La reescritura de historial es opcional y avanzada.)

---

## 🧩 Plantillas (placeholders)

Crea estos archivos para orientar a colaboradores sin exponer secretos:

**`.env.example`**

```env
# Backend / LLM
OLLAMA_URL=
MODEL_NAME=qwen2.5:1.5b-instruct
EMBED_MODEL=nomic-embed-text
CHUNK_SIZE=900
CHUNK_OVERLAP=120
TOP_K=4
# Opcional si proteges endpoints
API_KEY=
```

**`context/README.md`**

```md
Coloca aquí archivos .txt con contenido público o anonimizado para el RAG.
Formato sugerido: un archivo por sección. Evita datos personales/sensibles.
Ejemplo: introduccion.txt, proyectos.txt, publicaciones.txt
```

## 🧪 Desarrollo local

Basta con abrir `index.html` en el navegador o servir con un server estático (ej. `npx serve`).

```bash
# con npx serve (opcional)
npx serve . -l 5173
```

## 🚀 Despliegue a Firebase

1. **Build (si aplica)**: en vanilla no hay build. Si agregas bundler, compila a `dist/`.
2. **Inicializar Hosting (la primera vez)**

   ```bash
   firebase init hosting
   # ? Select a default Firebase project:  <elige tu proyecto>
   # ? What do you want to use as your public directory?  .  (o dist)
   # ? Configure as a single-page app (rewrite all urls to /index.html)?  y/n
   # ? Set up automatic builds and deploys with GitHub?  y/n
   ```
3. **Deploy**

   ```bash
   firebase deploy --only hosting
   ```

### Dominio propio

* En la consola de Firebase → *Hosting* → *Add custom domain*.
* Agrega los registros **A** y **AAAA** que te indique (p. ej. `ghs.googlehosted.com`).
* Verifica el dominio y espera propagación DNS.

## 🔌 Integración con backend

* Endpoint de salud: `GET /health` para verificar conectividad.
* Ajusta CORS en tu backend y usa HTTPS en prod.

## 🗺️ Roadmap

* [ ] Sección de blog/notes con Markdown
* [ ] Modo claro/oscuro con toggle
* [ ] Tests ligeros de UI
* [ ] Integración CI/CD con GitHub Actions

## 📸 Capturas

> *Coloca aquí imágenes de `assets/` cuando estén listas.*

## 🧩 Scripts útiles

```bash
# Lint rápido (si agregas ESLint)
npx eslint .
# Preview local con live reload
npx live-server
```

## 🧾 Licencia

[MIT](LICENSE)

## 👤 Autor

**Jorge Hewstone Correa** — ML Engineer
LinkedIn: [https://www.linkedin.com/in/jorgehewstone/](https://www.linkedin.com/in/jorgehewstone/)
Portfolio (live): [https://tu-dominio.com](https://tu-dominio.com)
