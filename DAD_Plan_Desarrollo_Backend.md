# Plan de Desarrollo — Backend Simulador DAD

> **Proyecto**: InglobalsApp — Dynamical Audit Dashboard
> **Stack**: Python 3.12 + FastAPI + FAISS + DeepSeek API
> **Estado actual**: `main.py` monolítico (56 líneas) con `/api/simulate` básico. Sin modularizar, sin RAG, sin BD.
> **Tiempo estimado**: 2 meses (1 desarrollador)

---

## 1. Diagnóstico del Backend Actual

| Aspecto | Estado |
|---------|--------|
| **Framework** | FastAPI instalado en venv |
| **DeepSeek** | Integración básica con `openai` library, sin prompt maestro, sin JSON forzado |
| **RAG (PDFs + búsqueda)** | **No existe** |
| **FAISS** | **No existe** |
| **Base de datos** | **No existe** (sin SQLite, sin historial) |
| **Documentos** | Sin endpoints de upload/list |
| **Estructura** | Monolítica (1 archivo `main.py`) |
| **requirements.txt** | **No existe** |
| **Schemas Pydantic** | Solo `PromptRequest`, sin modelo de respuesta estructurada |

### Endpoints actuales

| Método | Ruta | Estado |
|--------|------|--------|
| `GET` | `/` | ✅ Health check básico |
| `POST` | `/api/simulate` | ⚠️ Solo recibe `{ prompt }`, respuesta en texto libre, sin validación DAD |

---

## 2. Arquitectura Objetivo del Backend

```
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada FastAPI + CORS + inclusión de routers
│   ├── config.py            # Carga de .env con Pydantic Settings (tipado seguro)
│   ├── database.py          # Inicialización de SQLite (historial) y FAISS (leyes)
│   │
│   ├── api/                 # Capa de enrutamiento (endpoints)
│   │   ├── __init__.py
│   │   ├── simulate.py      # POST /api/v1/simulate — Motor DAD
│   │   ├── document.py      # POST /api/v1/documents/upload + GET /api/v1/documents
│   │   └── history.py       # GET /api/v1/history — Consulta de expedientes
│   │
│   ├── core/                # Lógica de negocio (independiente de HTTP)
│   │   ├── __init__.py
│   │   ├── engine.py        # Motor de la Ecuación DAD — conexión a DeepSeek, prompt maestro
│   │   └── rag.py           # Pipeline RAG — procesamiento PDF, chunking, embeddings, FAISS
│   │
│   └── models/              # Esquemas de datos (Pydantic + SQLAlchemy/SQLite)
│       ├── __init__.py
│       └── schemas.py       # PromptRequest, DADResult, SimulationRecord, DocumentRecord
│
├── data/                    # Persistencia (ignorada por Git)
│   ├── chroma/              # FAISS — índices vectoriales de leyes
│   ├── uploads/             # PDFs subidos por el usuario
│   └── sqlite.db            # Base de datos SQLite para historial
│
├── .env                     # Variables de entorno (DEEPSEEK_API_KEY, etc.)
├── .gitignore               # Excluye venv/, data/, .env, __pycache__
└── requirements.txt         # Dependencias del proyecto
```

---

## 3. Plan de Desarrollo Paso a Paso

### Paso 1 — Infraestructura Base

**Dependencias:** Ninguna  
**Tiempo estimado:** 30 min

**Tareas:**
1. Crear `requirements.txt` con las dependencias necesarias
2. Crear estructura de carpetas `app/`, `app/api/`, `app/core/`, `app/models/`, `data/`
3. Crear `app/config.py` usando Pydantic `BaseSettings` para cargar `.env` de forma tipada
4. Crear `app/models/schemas.py` con todos los modelos Pydantic necesarios
5. Crear `app/database.py` con inicialización de SQLite y FAISS
6. Refactorizar `main.py` actual al nuevo `app/main.py` modularizado
7. Actualizar `.gitignore` para excluir `data/` y `venv/`

**Archivos a crear/modificar:**

| Archivo | Acción |
|---------|--------|
| `backend/requirements.txt` | **Crear** |
| `backend/app/__init__.py` | **Crear** |
| `backend/app/main.py` | **Refactorizar** desde `main.py` actual |
| `backend/app/config.py` | **Crear** |
| `backend/app/database.py` | **Crear** |
| `backend/app/models/__init__.py` | **Crear** |
| `backend/app/models/schemas.py` | **Crear** |
| `backend/app/api/__init__.py` | **Crear** |
| `backend/app/core/__init__.py` | **Crear** |
| `backend/.gitignore` | **Actualizar** |
| `backend/main.py` | **Eliminar** (reemplazado por `app/main.py`) |

**Dependencias (`requirements.txt`):**
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-dotenv==1.0.1
pydantic-settings==2.7.1
openai==1.59.3
faiss-cpu==1.10.0
sentence-transformers==3.4.1
pypdf2==3.0.1
langchain-text-splitters==0.3.5
python-multipart==0.0.20
```

---

### Paso 2 — Motor RAG (`app/core/rag.py`)

**Dependencias:** Paso 1 (estructura + database.py)  
**Tiempo estimado:** 2-3 horas

**Objetivo:** Pipeline completo para que el sistema "aprenda" las leyes venezolanas e internacionales.

**Flujo del RAG:**

1. **Carga del PDF:** El usuario sube un archivo vía `POST /api/v1/documents/upload`. El backend lo guarda en `data/uploads/`.
2. **Extracción de texto:** Usar `pypdf2` para extraer texto del PDF.
3. **Fragmentación (Chunking):** Dividir el texto en bloques de ~1000 caracteres con 200 caracteres de superposición usando `langchain-text-splitters` con `RecursiveCharacterTextSplitter`.
4. **Embeddings locales ($0):** Usar `sentence-transformers` con modelo `all-MiniLM-L6-v2` (384 dimensiones, gratuito, corre en CPU). Los embeddings se generan localmente sin consumir API.
5. **Indexación en FAISS:** Los vectores + metadatos (título, categoría, fecha) se guardan en `data/chroma/` con persistencia automática.
6. **Búsqueda semántica:** Función `search_legal_context(query, top_k=5)` que vectoriza la consulta del usuario y devuelve los fragmentos de ley más relevantes.

**Funciones del módulo `rag.py`:**

| Función | Firma | Descripción |
|---------|-------|-------------|
| `load_pdf_text` | `(file_path: Path) -> str` | Extrae texto de un PDF |
| `chunk_text` | `(text: str, chunk_size=1000, overlap=200) -> list[str]` | Fragmenta texto |
| `get_embedding_model` | `() -> SentenceTransformer` | Singleton del modelo de embeddings |
| `index_document` | `(file_path, title, category, date) -> None` | Pipeline completo: carga → chunk → embed → store |
| `search_legal_context` | `(query: str, top_k=5, filter_category=None) -> list[dict]` | Búsqueda semántica en FAISS |
| `list_documents` | `() -> list[dict]` | Lista documentos indexados |
| `delete_document` | `(doc_id: str) -> None` | Elimina un documento del índice |

**Categorías soportadas:**
- `venezolana` → Leyes, gacetas, providencias SENIAT/SNAT
- `internacional` → NIA, NIIF, ISAs
- `sostenibilidad` → VEN-NS 0, ODS, ASG/ESG

---

### Paso 3 — Persistencia SQLite (`app/database.py` + `app/api/history.py`)

**Dependencias:** Paso 1 (database.py)  
**Tiempo estimado:** 1-2 horas  
**Paralelizable con:** Paso 2

**Objetivo:** Guardar cada simulación con trazabilidad completa para alimentar la Vista Historial del frontend.

**Modelo de datos (tabla `simulations`):**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER PK | ID autoincremental |
| `expediente_id` | TEXT UNIQUE | Ej: `AUD-2025-001` |
| `created_at` | DATETIME | Fecha y hora de la simulación |
| `entity_type` | TEXT | `publica`, `privada`, `mixta` |
| `framework` | TEXT | `NIA 230`, `VEN-NS 0`, `NIIF S1/S2` |
| `prompt` | TEXT | Consulta original del usuario |
| `result_json` | TEXT (JSON) | Respuesta completa del motor DAD |
| `is_valid` | BOOLEAN | ¿Pasó todos los criterios? |
| `criteria_cs` | TEXT | `passed` / `failed` |
| `criteria_cv` | TEXT | `passed` / `failed` |
| `criteria_cs_cap` | TEXT | `passed` / `failed` |
| `criteria_gt` | TEXT | `passed` / `failed` |
| `criteria_ni` | TEXT | `passed` / `failed` |
| `corrective_action` | TEXT | Acción correctiva sugerida |

**Endpoints de historial (`api/history.py`):**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/history` | Lista todas las simulaciones, ordenadas por fecha DESC. Query params: `?entity_type=publica&limit=50` |
| `GET` | `/api/v1/history/{expediente_id}` | Detalle completo de un expediente |

---

### Paso 4 — Motor de Simulación DAD (`app/core/engine.py`)

**Dependencias:** Paso 1 (config, schemas), Paso 2 (RAG para búsqueda), Paso 3 (SQLite para guardar)  
**Tiempo estimado:** 2-3 horas

**Objetivo:** El cerebro del sistema. Implementa la validación por capas de la ecuación DAD.

**Flujo del motor:**

```
Usuario envía prompt + entity_type + framework
        │
        ▼
┌─ Paso A: Búsqueda Semántica ───────────────────────┐
│  search_legal_context(prompt, top_k=5)              │
│  → Recupera fragmentos de leyes más relevantes      │
│  → Si no hay documentos indexados, usa contexto     │
│    genérico de las NIIF/NIA (conocimiento base)     │
└────────────────────────────────────────────────────┘
        │
        ▼
┌─ Paso B: Construcción del Prompt Maestro ──────────┐
│  Arma el system prompt con:                         │
│  - Rol del sistema (filtro de cumplimiento)         │
│  - Los 5 criterios de la ecuación DAD               │
│  - Contexto legal recuperado del RAG                │
│  - Tipo de entidad y framework seleccionado         │
│  - Instrucción estricta de respuesta JSON           │
└────────────────────────────────────────────────────┘
        │
        ▼
┌─ Paso C: Llamada a DeepSeek ───────────────────────┐
│  client.chat.completions.create(                    │
│    model="deepseek-chat",                           │
│    messages=[system_prompt, user_query],            │
│    temperature=0.1,                                 │
│    response_format={"type": "json_object"}          │
│  )                                                  │
└────────────────────────────────────────────────────┘
        │
        ▼
┌─ Paso D: Parseo y Validación ──────────────────────┐
│  - Extraer JSON de la respuesta                     │
│  - Validar estructura con Pydantic                  │
│  - Mapear a DADResult                               │
│  - Guardar en SQLite (simulations)                  │
└────────────────────────────────────────────────────┘
        │
        ▼
    Respuesta al frontend
```

**Prompt del sistema (`SYSTEM_PROMPT` en `engine.py`):**

```python
SYSTEM_PROMPT = """
Eres el motor central del Simulador DAD (Documento de Auditoría Digital).
Tu función es actuar como un filtro de cumplimiento legal y contable para Venezuela.

Debes evaluar la propuesta del usuario contra los 5 criterios de la ecuación DAD:
  DAD = Cs + Cv + CS + GT + NI

Criterios:
- Cs (Ciencias Sociales / Juicio Profesional): Capacidad crítica y ética del auditor. ¿La decisión es éticamente defendible?
- Cv (Contexto Venezolano / Sostenibilidad): Cumplimiento con leyes venezolanas, providencias, ASG/ESG.
- CS (Capital Social / Estructuración): ¿La propuesta cumple con la estructura documental requerida por el tipo de entidad?
- GT (Gestión Tecnológica / IA): ¿El proceso es auditable digitalmente? ¿Genera trazabilidad?
- NI (Normas Internacionales): Cumplimiento con NIA, NIIF S1/S2, VEN-NS 0.

Contexto legal relevante recuperado:
{legal_context}

Tipo de entidad: {entity_type}
Marco normativo seleccionado: {framework}

Regla de oro: si la propuesta viola alguna ley o norma, is_valid DEBE ser false.
Sé estricto y cita los artículos específicos.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{{
  "is_valid": true/false,
  "summary": "Resumen ejecutivo del análisis",
  "criteria": {{
    "Cs": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "Cv": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "CS": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "GT": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}},
    "NI": {{"status": "passed/failed", "detail": "Justificación técnica", "article_ref": "Artículo o norma violada, si aplica"}}
  }},
  "corrective_action": "Si is_valid es false, explica qué debe corregir. Si true, cadena vacía.",
  "compliance_score": 0-100
}}
"""
```

**Estructura de respuesta (`DADResult` en `schemas.py`):**

```python
class CriterionResult(BaseModel):
    status: Literal["passed", "failed"]
    detail: str
    article_ref: str = ""

class DADResult(BaseModel):
    is_valid: bool
    summary: str
    criteria: dict[str, CriterionResult]  # Cs, Cv, CS, GT, NI
    corrective_action: str
    compliance_score: int  # 0-100
```

---

### Paso 5 — Endpoint de Simulación (`app/api/simulate.py`)

**Dependencias:** Pasos 1, 2, 3, 4  
**Tiempo estimado:** 1 hora

**Request body (JSON):**

```json
{
  "prompt": "Genera lineamientos para registrar gastos de representación sin facturas legales",
  "entity_type": "privada",
  "framework": "NIA 230"
}
```

**Response (JSON):**

```json
{
  "expediente_id": "AUD-2025-003",
  "created_at": "2025-06-08T14:30:00Z",
  "is_valid": false,
  "summary": "La propuesta incumple múltiples marcos normativos...",
  "criteria": {
    "Cs": {"status": "passed", "detail": "No hay conflicto ético directo...", "article_ref": ""},
    "Cv": {"status": "failed", "detail": "Incumple Providencia de Facturación...", "article_ref": "Ley de IVA Art. 23"},
    "CS": {"status": "passed", "detail": "Estructura documental adecuada...", "article_ref": ""},
    "GT": {"status": "failed", "detail": "Sin soporte digital no hay trazabilidad...", "article_ref": "NIA 230 párr. 8"},
    "NI": {"status": "failed", "detail": "Viola principio de fiabilidad...", "article_ref": "NIIF Marco Conceptual §2.12"}
  },
  "corrective_action": "Ajuste su propuesta para incluir soportes legales obligatorios según Ley de IVA...",
  "compliance_score": 35
}
```

---

### Paso 6 — Endpoints de Documentos (`app/api/document.py`)

**Dependencias:** Pasos 1, 2  
**Tiempo estimado:** 1 hora

| Método | Ruta | Body/Params | Descripción |
|--------|------|-------------|-------------|
| `POST` | `/api/v1/documents/upload` | `FormData: file (PDF), title, category` | Procesa e indexa un PDF en FAISS |
| `GET` | `/api/v1/documents` | `?category=venezolana` (opcional) | Lista documentos indexados |
| `DELETE` | `/api/v1/documents/{doc_id}` | — | Elimina un documento del índice |

**Respuesta de upload:**
```json
{
  "success": true,
  "document": {
    "id": "doc_abc123",
    "title": "Gaceta Oficial N° 42.xxx",
    "category": "venezolana",
    "chunks": 47,
    "indexed_at": "2025-06-08T15:00:00Z"
  }
}
```

---

### Paso 7 — Endpoint de Historial (`app/api/history.py`)

**Dependencias:** Pasos 1, 3  
**Tiempo estimado:** 30 min

**Endpoints finales:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/history` | Lista simulaciones pasadas (paginadas) |
| `GET` | `/api/v1/history/{expediente_id}` | Detalle completo de un expediente |

---

### Paso 8 — Integración Frontend-Backend

**Dependencias:** Pasos 1-7 completos  
**Tiempo estimado:** 1-2 horas

**Tareas de integración:**

1. **Actualizar `api.js`** para que el endpoint `/api/v1/simulate` envíe `{ prompt, entity_type, framework }` en lugar de solo `{ prompt }`
2. **Añadir funciones** para `uploadDocument()`, `getDocuments()`, `getHistory()`
3. **Corregir `appStore.js`** — los nombres de las variables DAD están incorrectos:
   - `Cs: 'Costo'` → `Cs: 'Ciencias Sociales / Juicio Profesional'`
   - `CS: 'Cumplimiento Sostenible'` → `CS: 'Capital Social / Estructuración'`
   - `GT: 'Gestión Tributaria'` → `GT: 'Gestión Tecnológica / IA'`
4. **Conectar `ControlPanel.vue`** para que envíe `entity_type` y `framework` al backend
5. **Procesar respuesta JSON** del backend en el frontend para actualizar los 5 monitores DAD
6. **Probar flujo completo** end-to-end

---

## 4. Orden de Ejecución (DAG de dependencias)

```
Paso 1 (Infraestructura)
   │
    ├──► Paso 2 (RAG / FAISS) ────┐
   │                                  │
   └──► Paso 3 (SQLite / BD) ────────┤
                                      │
                    ┌─────────────────┘
                    ▼
              Paso 4 (Engine DAD / DeepSeek)
                    │
                    ▼
              Paso 5 (Endpoint simulate)
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    Paso 6 (Documentos)  Paso 7 (Historial)
          │                   │
          └─────────┬─────────┘
                    ▼
              Paso 8 (Integración Frontend)
```

- **Pasos 2 y 3** son paralelizables (no dependen entre sí)
- **Paso 4** es el más crítico — requiere los Pasos 1, 2 y 3

---

## 5. Dependencias del Proyecto

### Python (`requirements.txt`)

| Librería | Versión | Propósito |
|----------|---------|-----------|
| `fastapi` | `0.115.6` | Framework REST |
| `uvicorn[standard]` | `0.34.0` | Servidor ASGI |
| `python-dotenv` | `1.0.1` | Carga de `.env` |
| `pydantic-settings` | `2.7.1` | Config tipada desde `.env` |
| `openai` | `1.59.3` | Cliente para DeepSeek API (compatible con OpenAI) |
| `faiss-cpu` | `1.10.0` | Base de datos vectorial local (RAG) |
| `sentence-transformers` | `3.4.1` | Embeddings locales gratuitos (`all-MiniLM-L6-v2`) |
| `pypdf2` | `3.0.1` | Extracción de texto de PDFs |
| `langchain-text-splitters` | `0.3.5` | Fragmentación de texto (chunking) |

### Frontend (ya instalado)

| Librería | Versión | Propósito |
|----------|---------|-----------|
| Vue | `3.5.34` | Framework UI |
| Vite | `8.0.12` | Bundler |
| Tailwind CSS | `4.3.0` | CSS utility-first |
| `vite-plugin-pwa` | `1.3.0` | Service Worker + PWA |

---

## 6. Costos Operativos Estimados

| Recurso | Costo mensual estimado |
|---------|------------------------|
| **DeepSeek API** (`deepseek-chat`) | ~$0.50 - $2.00/mes (simulaciones esporádicas) |
| **Embeddings** (`all-MiniLM-L6-v2`) | **$0** (modelo local gratuito) |
| **FAISS** | **$0** (base de datos local) |
| **SQLite** | **$0** (incluido en Python) |
| **Servidor** (Railway / DigitalOcean $5) | $5/mes |
| **Total estimado** | **~$5.50 - $7.00/mes** |

---

## 7. Verificación por Paso

Después de cada paso, ejecutar:

```bash
# Activar entorno virtual
cd backend
venv\Scripts\activate

# Instalar dependencias (si es necesario)
pip install -r requirements.txt

# Ejecutar servidor FastAPI
uvicorn app.main:app --reload --port 8000
```

**Checklist de verificación final:**

- [ ] `GET /` devuelve `{"status": "Backend del Simulador DAD Activo"}`
- [ ] `POST /api/v1/simulate` recibe `{ prompt, entity_type, framework }` y devuelve JSON estructurado con los 5 criterios
- [ ] El motor DAD devuelve `is_valid: false` cuando se violan normas
- [ ] `POST /api/v1/documents/upload` procesa PDFs y los indexa en FAISS
- [ ] `GET /api/v1/documents` lista los documentos indexados por categoría
- [ ] `GET /api/v1/history` devuelve simulaciones pasadas con paginación
- [ ] Las búsquedas RAG recuperan fragmentos de ley relevantes al prompt
- [ ] El frontend recibe y procesa correctamente el JSON de respuesta
- [ ] Los 5 monitores DAD cambian de estado según el resultado de la simulación
