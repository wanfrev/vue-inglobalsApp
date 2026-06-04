# Plan de Reestructuración — PWA DAD (Dynamical Audit Dashboard)

> **Cliente**: InglobalsApp  
> **Framework**: Vue 3 + Vite + Tailwind CSS v4  
> **Estado**: MVP — 3 vistas, navegación reactiva sin router, PWA offline-ready

---

## 1. Diagnóstico del Estado Actual

| Aspecto | Estado |
|---------|--------|
| **Framework** | Vue 3 + Vite |
| **CSS** | Tailwind CSS v4.3.0 (instalado, usa sintaxis v3 heredada) |
| **Ruteo** | Ninguno — se migrará a estado reactivo `ref()` |
| **PWA** | `vite-plugin-pwa` instalado, sin configurar |
| **Views** | `src/views/` — vacío |
| **Componentes** | Solo `HelloWorld.vue` (template por defecto de Vite) |
| **Servicios** | `src/services/` — vacío |
| **Store** | No existe — se creará `stores/appStore.js` |

---

## 2. Arquitectura de la Aplicación

### Mapa de Vistas

```
[Login / Acceso Seguro] (futuro)
         │
         ▼
[Vista Principal: Emulador] ───► (Si falla) ───► [Alerta de Rebote Explicativa]
         │
         ├───► [Vista Repositorio] ───► [Cargar / Ver PDFs de Leyes]
         │
         └───► [Vista Historial] ───► [Descargar Memoria Técnica DAD en PDF]
```

### Navegación (Bottom Nav / Sidebar)

- **Móvil**: Barra inferior fija con 3 íconos + label
- **Escritorio**: Sidebar lateral izquierdo colapsable
- **Mecanismo**: Estado reactivo `const currentView = ref('emulator')` en `appStore.js`
- **Sin dependencias externas**: íconos SVG inline, sin librerías de iconos

---

## 3. Estructura de Archivos Final

```
frontend/src/
│
├── App.vue                         # Shell principal + switching de vistas
├── main.js                         # Entry point (sin cambios)
├── style.css                       # Tailwind v4 + @theme con tokens personalizados
│
├── components/
│   ├── layout/
│   │   ├── AppNav.vue              # Bottom navigation / Sidebar
│   │   └── AppHeader.vue           # Barra: entidad + leyes activas
│   │
│   ├── emulator/
│   │   ├── DADMonitor.vue          # 1 indicador visual DAD
│   │   ├── DADPanel.vue            # 5 monitores ($Cs, Cv, CS, GT, NI)
│   │   ├── ControlPanel.vue        # Selectores: entidad + marco normativo
│   │   └── ChatFeed.vue            # Feed estilo chat + input
│   │
│   ├── repository/
│   │   ├── DocCard.vue             # Tarjeta de documento legal
│   │   └── DocUploader.vue         # Modal de carga PDF
│   │
│   └── history/
│       ├── HistoryTable.vue        # Tabla de simulaciones
│       └── ReportCard.vue          # Detalle de expediente
│
├── views/
│   ├── EmulatorView.vue            # Vista 1: El Emulador Virtual (Home)
│   ├── RepositoryView.vue          # Vista 2: Repositorio Normativo (RAG)
│   └── HistoryView.vue             # Vista 3: Historial y Memoria Técnica
│
├── services/
│   └── api.js                      # Cliente HTTP (fetch wrapper)
│
└── stores/
    └── appStore.js                 # Estado global reactivo
```

---

## 4. Sistema de Diseño (Tailwind v4 Nativo)

### Migración desde v3 heredado

- Se elimina `tailwind.config.js`
- Se elimina `postcss.config.js`
- Se reemplaza el contenido de `style.css`

### Tokens de Color

```css
@import "tailwindcss";

@theme {
  --color-navy-900: #0a1628;
  --color-navy-800: #0f1d3a;
  --color-navy-700: #162a50;
  --color-navy-600: #1e3a8a;     /* Primary actions */
  --color-navy-500: #2563eb;     /* Hover / Accent */

  --color-slate-950: #020617;
  --color-slate-900: #0f172a;
  --color-slate-800: #1e293b;
  --color-slate-700: #334155;
  --color-slate-600: #475569;
  --color-slate-400: #94a3b8;
  --color-slate-300: #cbd5e1;
  --color-slate-100: #f1f5f9;

  --color-emerald: #10b981;      /* Aprobación */
  --color-crimson: #dc2626;      /* Rebote normativo */
  --color-amber:   #f59e0b;      /* Procesando / advertencia */
}
```

### Look & Feel

| Elemento | Color |
|----------|-------|
| Fondo general | `slate-950` |
| Superficies / tarjetas | `slate-900` / `slate-800` |
| Texto primario | `slate-100` |
| Texto secundario | `slate-400` |
| Botones primarios | `navy-600` (hover: `navy-500`) |
| Éxito / aprobación | `emerald` |
| Error / rebote | `crimson` |
| Procesando | `amber` |
| Bordes / separadores | `slate-700` / `slate-600` |

### Principios de UI/UX

- **Mobile-first**: botones grandes, menús colapsables, tablas legibles en vertical
- **Look corporativo/ejectuvio**: sin colores juveniles, grises oscuros dominan
- **Visibilidad de estado**: el usuario siempre sabe qué entidad audita y qué leyes están activas (`AppHeader`)
- **Feedback inmediato**: los monitores DAD cambian de color en tiempo real

---

## 5. Almacén de Estado Global (`appStore.js`)

Estado reactivo compartido entre todos los componentes:

```javascript
import { reactive, ref } from 'vue'

// Vista activa
const currentView = ref('emulator')  // 'emulator' | 'repository' | 'history'

// Configuración del Emulador
const entityType  = ref('publica')   // 'publica' | 'privada' | 'mixta'
const activeLaws  = ref([])          // Ej: ['NIA 230', 'VEN-NS 0', 'NIIF S1/S2']

// Estado de la simulación
const simulationStatus = ref('idle')  // 'idle' | 'processing' | 'success' | 'error'
const dadVariables     = reactive({
  Cs:  { label: 'Cs',  status: 'idle' },  // Costo
  Cv:  { label: 'Cv',  status: 'idle' },  // Contexto Venezolano
  CS:  { label: 'CS',  status: 'idle' },  // Cumplimiento Sostenible
  GT:  { label: 'GT',  status: 'idle' },  // Gestión Tributaria
  NI:  { label: 'NI',  status: 'idle' },  // Normativa Internacional
})

// Historial
const simulationHistory = ref([])

// Repositorio
const documents = ref([])
```

---

## 6. Vista 1: Emulador Virtual (Home)

### Layout

```
┌──────────────────────────────────┐
│        AppHeader                 │
│  Entidad: Pública  │  Leyes: NIA 230 │
├──────────────────────────────────┤
│  ┌──── DADPanel ──────────────┐  │
│  │ [$Cs] [$Cv] [$CS] [$GT] [$NI] │ │
│  └────────────────────────────┘  │
│                                  │
│  ┌── ControlPanel ────────────┐  │
│  │ Entidad: [Pública    ▾]    │  │
│  │ Norma:   [NIA 230    ▾]    │  │
│  │                  [▶ Simular] │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌── ChatFeed ────────────────┐  │
│  │ Usuario: auditar balance   │  │
│  │ DAD:    análisis completo  │  │
│  │                            │  │
│  │ ⚠ Alerta de Rebote        │  │
│  │ Cv (Contexto Venezolano)   │  │
│  │ falló en el criterio X.    │  │
│  │                            │  │
│  │ [Escribe tu consulta...] ➤ │  │
│  └────────────────────────────┘  │
├──────────────────────────────────┤
│         AppNav (bottom nav)      │
└──────────────────────────────────┘
```

### Comportamiento de Monitores DAD

| Estado | Visual | Descripción |
|--------|--------|-------------|
| `idle` | Gris (`slate-700`) | Monitor en reposo |
| `processing` | Amarillo (`amber`) + fade animado | Simulación en curso |
| `success` | Verde (`emerald`) | Variable aprobada |
| `error` | Rojo (`crimson`) + alerta en chat | Variable reprobada |

### Componentes

#### `DADMonitor.vue`
- Props: `label`, `status`
- Render: círculo o barra con el label y color según status
- Animación CSS en estado `processing` (pulso suave)

#### `DADPanel.vue`
- Renderiza 5 `DADMonitor` en fila (responsive: wrap en móvil)
- Lee estado de `dadVariables` desde `appStore`

#### `ControlPanel.vue`
- `<select>` para tipo de entidad (Pública, Privada, Mixta)
- `<select>` para marco normativo (NIA 230, VEN-NS 0, NIIF S1/S2)
- Botón "Simular" → dispara simulación, activa monitores

#### `ChatFeed.vue`
- Lista de mensajes (usuario + respuestas DAD)
- Input de texto + botón de envío
- Soporte para alertas de rebote estructuradas (componente de alerta roja)
- Auto-scroll al último mensaje

---

## 7. Vista 2: Repositorio Normativo (RAG)

### Layout

```
┌──────────────────────────────────┐
│  Repositorio Normativo           │
│  [🔍 Buscar documento...]       │
├──────────────────────────────────┤
│                                  │
│  ┌─ Categoría: Venezolana ───┐  │
│  │ ┌── DocCard ────────────┐  │  │
│  │ │ Gaceta Oficial N° 42.xxx │  │
│  │ │ Actualizado: 15/01/2025  │  │
│  │ │ [Ver fuente]             │  │
│  │ └────────────────────────┘  │  │
│  │ ┌── DocCard ────────────┐  │  │
│  │ │ SENIAT Providencia... │  │  │
│  │ │ Actualizado: 02/03/2025  │  │
│  │ │ [Ver fuente]             │  │
│  │ └────────────────────────┘  │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌─ Categoría: Internacional ─┐ │
│  │ ┌── DocCard ────────────┐  │ │
│  │ │ NIA 230 — Documentación│  │ │
│  │ │ Actualizado: 01/12/2024  │  │
│  │ │ [Ver fuente]             │  │
│  │ └────────────────────────┘  │ │
│  └────────────────────────────┘  │
│                                  │
│  ┌─ Categoría: Sostenibilidad ┐ │
│  │ ┌── DocCard ────────────┐  │ │
│  │ │ VEN-NS 0 / ODS         │  │ │
│  │ │ Actualizado: 10/11/2024  │  │
│  │ │ [Ver fuente]             │  │
│  │ └────────────────────────┘  │ │
│  └────────────────────────────┘  │
│                                  │
│       [＋ Cargar Documento]      │  ← FAB
└──────────────────────────────────┘
```

### Componentes

#### `DocCard.vue`
- Props: `title`, `date`, `category`, `sourceUrl`
- Badge de categoría con color distintivo
- Botón "Ver fuente" → abre PDF en nueva pestaña o visor embebido

#### `DocUploader.vue`
- Modal overlay
- Drag & drop de archivos PDF
- Campos: nombre, categoría, archivo
- Botón "Subir"

---

## 8. Vista 3: Historial de Expedientes

### Layout

```
┌──────────────────────────────────┐
│  Historial y Memoria Técnica     │
├──────────────────────────────────┤
│                                  │
│  ┌── HistoryTable ────────────┐  │
│  │ Fecha    │ Entidad │ Solicitud │ │
│  │ ─────────────────────────── │  │
│  │ 12/05/25 │ Pública │ Audit... │  │
│  │          │         │ ██████░ │  │
│  │          │         │ 83%     │  │
│  │          │         │ [PDF]   │  │
│  │ ─────────────────────────── │  │
│  │ 10/05/25 │ Privada │ Balan... │  │
│  │          │         │ █████░░ │  │
│  │          │         │ 55%     │  │
│  │          │         │ [PDF]   │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌── ReportCard (expandido) ──┐  │
│  │ Expediente #AUD-2025-001   │  │
│  │ Entidad: Pública           │  │
│  │ Fecha: 12/05/2025          │  │
│  │ Leyes aplicadas: NIA 230   │  │
│  │                            │  │
│  │ Resultados DAD:            │  │
│  │ ✓ Cs — ✔ Aprobado         │  │
│  │ ✗ Cv — ❌ Rebotado (Art. 7)│  │
│  │ ✓ CS — ✔ Aprobado         │  │
│  │ ✓ GT — ✔ Aprobado         │  │
│  │ ✓ NI — ✔ Aprobado         │  │
│  │                            │  │
│  │ [📄 Descargar Certificado] │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### Componentes

#### `HistoryTable.vue`
- Columnas: Fecha, Entidad, Solicitud, Nivel de Cumplimiento, Acciones
- Barra de progreso en celda "Cumplimiento"
- Botón "Exportar Certificado DAD" por fila
- Click en fila → expande `ReportCard.vue`

#### `ReportCard.vue`
- Vista detallada del expediente
- Desglose variable por variable de la ecuación DAD
- Botón "Descargar Certificado DAD" → genera PDF

---

## 9. Stack Técnico

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Vue | ^3.5 | Framework UI |
| Vite | ^8.0 | Bundler + dev server |
| Tailwind CSS | ^4.3 | Utility-first CSS |
| vite-plugin-pwa | ^1.3 | Service worker + manifest PWA |
| JavaScript (Vanilla) | — | Sin TypeScript ni librerías externas pesadas |

**Exclusiones deliberadas:**
- Sin Vue Router → navegación por estado reactivo
- Sin Pinia → store propio con `reactive()` / `ref()` (escala bien para MVP)
- Sin Axios → `fetch` nativo (menos peso)
- Sin librerías de iconos → SVG inline
- Sin librerías de PDF (se evalúa `html2pdf.js` o similar liviano para exportación futura)

---

## 10. Configuración PWA

En `vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'DAD — Dynamical Audit Dashboard',
        short_name: 'DAD',
        description: 'Tablero de comandos de auditoría legal con simulación DAD',
        theme_color: '#0f172a',
        background_color: '#020617',
        display: 'standalone',
        orientation: 'portrait',
        icons: [
          {
            src: 'icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ]
})
```

---

## 11. Orden de Implementación (8 Pasos)

| # | Paso | Archivos a crear/modificar | Descripción |
|---|------|---------------------------|-------------|
| 1 | **Migrar a Tailwind v4** | `style.css` (crear), eliminar `tailwind.config.js`, `postcss.config.js` | Reemplazar directivas `@tailwind` por `@import "tailwindcss"` + `@theme` |
| 2 | **Crear store global** | `stores/appStore.js` | Estado reactivo: `currentView`, `entityType`, `activeLaws`, `dadVariables` |
| 3 | **Navegación + Layout base** | `App.vue` (reescribir), `AppNav.vue`, `AppHeader.vue` | Shell con bottom nav, sidebar desktop, header informativo |
| 4 | **Vista Emulador** | `EmulatorView.vue`, `DADMonitor.vue`, `DADPanel.vue`, `ControlPanel.vue`, `ChatFeed.vue` | Feed tipo chat + monitores + controles |
| 5 | **Vista Repositorio** | `RepositoryView.vue`, `DocCard.vue`, `DocUploader.vue` | Grid de documentos + carga PDF |
| 6 | **Vista Historial** | `HistoryView.vue`, `HistoryTable.vue`, `ReportCard.vue` | Tabla + detalle + exportación |
| 7 | **Servicio API** | `services/api.js` | Wrapper fetch para comunicación con backend |
| 8 | **Configurar PWA** | `vite.config.js` | Plugin `VitePWA` con manifest y service worker |

---

## 12. Verificación

Después de cada paso, ejecutar:

```bash
npm run dev
```

Checklist de verificación final:

- [ ] Compilación sin errores
- [ ] Navegación entre las 3 vistas desde bottom nav
- [ ] Monitores DAD cambian de estado (idle → processing → success/error)
- [ ] Alerta de rebote se muestra en chatfeed cuando una variable falla
- [ ] Documentos se renderizan en grid con categorías
- [ ] Carga de PDF (funcionalidad básica)
- [ ] Historial muestra tabla con datos de ejemplo
- [ ] Layout responsive: bottom nav en móvil, sidebar en escritorio
- [ ] PWA: manifest válido, tema oscuro, `display: standalone`
