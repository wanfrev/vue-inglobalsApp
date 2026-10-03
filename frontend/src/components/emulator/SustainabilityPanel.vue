<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  sustainability: { type: Object, required: true },
  // Afirmaciones del Loop 1: verificadas vs descartadas (falsabilidad 3/3).
  verification: { type: Object, default: () => ({ verified: 0, discarded: 0 }) },
  // % de palabras que el Loop 2 podó respecto al borrador lógico.
  pruningPercent: { type: Number, default: 0 },
})

const s = computed(() => props.sustainability)
const loops = computed(() => s.value.loops || [])

const fmtInt = (n) => Number(n || 0).toLocaleString('es')
const fmtUsd = (n) => {
  const v = Number(n || 0)
  if (v === 0) return '$0'
  return v < 0.01 ? `$${v.toFixed(4)}` : `$${v.toFixed(3)}`
}
const fmtDec = (n, d = 2) => Number(n || 0).toFixed(d)
const fmtCo2 = (n) => fmtDec(n, Number(n || 0) < 1 ? 3 : 2)

const overBudget = (total, budget) => budget > 0 && total > budget
const ratio = (total, budget) => (budget > 0 ? total / budget : 0)

// --- Panel de KPI (a pedido del cliente: mismo tipo de gráficas que el panel
// de sostenibilidad de referencia — barras con línea, torta con porcentajes,
// barras por categoría y medidor con aguja) ---------------------------------
// Color = el PASO (Reformulación / Loop 1 / Loop 2), igual en todas las
// gráficas (el color sigue a la entidad, nunca se reasigna). Paleta categórica
// fija de marca, validada para fondo claro con validate_palette.js --mode light.
const STEP_COLOR = {
  'Reformulación': 'var(--color-violetaIA)',
  'Loop 1': 'var(--color-oro)',
  'Loop 2': 'var(--color-verdeEsm)',
}
const SHORT_STEP = { 'Reformulación': 'Reform.', 'Loop 1': 'Loop 1', 'Loop 2': 'Loop 2' }

const steps = computed(() =>
  loops.value.map((l) => ({
    ...l,
    short: SHORT_STEP[l.name] || l.name,
    color: STEP_COLOR[l.name] || '#94a3b8',
  })),
)

function niceMax(raw) {
  if (!(raw > 0)) return 1
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  return Math.ceil(raw / magnitude) * magnitude
}
function tickLabel(v, prefix = '') {
  if (v === 0) return `${prefix}0`
  if (v >= 1000) return `${prefix}${Number((v / 1000).toFixed(1))}K`
  if (v < 1) return `${prefix}${Number(v.toPrecision(2))}`
  return `${prefix}${Number(v.toFixed(2))}`
}

// --- Barras por paso (+ línea acumulada en tokens: misma escala, un solo eje)
const BW = 260
const BH = 176
const PAD = { left: 40, right: 12, top: 14, bottom: 38 }
const plotW = BW - PAD.left - PAD.right
const plotH = BH - PAD.top - PAD.bottom
const BAR_W = 26

function barPath(x, y, w, h) {
  const r = Math.min(4, h)
  return `M ${x} ${y + h} L ${x} ${y + r} Q ${x} ${y} ${x + r} ${y} L ${x + w - r} ${y} Q ${x + w} ${y} ${x + w} ${y + r} L ${x + w} ${y + h} Z`
}

// Curva suave que no "rebota" (Fritsch–Carlson): no inventa valores intermedios.
function smoothPath(points) {
  const n = points.length
  if (n < 2) return ''
  const dx = []
  const m = []
  for (let i = 0; i < n - 1; i++) {
    dx.push(points[i + 1].x - points[i].x)
    m.push((points[i + 1].y - points[i].y) / dx[i])
  }
  const t = [m[0]]
  for (let i = 1; i < n - 1; i++) t.push(m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2)
  t.push(m[n - 2])
  for (let i = 0; i < n - 1; i++) {
    if (m[i] === 0) { t[i] = 0; t[i + 1] = 0; continue }
    const a = t[i] / m[i]
    const b = t[i + 1] / m[i]
    const h = a * a + b * b
    if (h > 9) {
      const k = 3 / Math.sqrt(h)
      t[i] = k * a * m[i]
      t[i + 1] = k * b * m[i]
    }
  }
  let d = `M ${points[0].x} ${points[0].y}`
  for (let i = 0; i < n - 1; i++) {
    const step = dx[i] / 3
    d += ` C ${points[i].x + step} ${points[i].y + t[i] * step}, ${points[i + 1].x - step} ${points[i + 1].y - t[i + 1] * step}, ${points[i + 1].x} ${points[i + 1].y}`
  }
  return d
}

function buildBarPanel(def) {
  const list = steps.value
  const n = Math.max(1, list.length)
  const values = list.map(def.get)
  const total = values.reduce((a, b) => a + b, 0)
  const cumulative = []
  values.reduce((acc, v, i) => { cumulative[i] = acc + v; return acc + v }, 0)
  const max = niceMax(def.cumulative ? Math.max(0, ...cumulative) : Math.max(0, ...values))
  const band = plotW / n
  const yOf = (v) => PAD.top + plotH - (v / max) * plotH

  const bars = list.map((st, i) => {
    const value = values[i]
    const h = Math.max(value > 0 ? 1.5 : 0, (value / max) * plotH)
    const x = PAD.left + band * i + (band - BAR_W) / 2
    return {
      name: st.name,
      short: st.short,
      color: st.color,
      value,
      pct: total > 0 ? Math.round((value / total) * 100) : 0,
      cx: x + BAR_W / 2,
      path: h > 0 ? barPath(x, PAD.top + plotH - h, BAR_W, h) : '',
      bandX: PAD.left + band * i,
    }
  })

  let line = null
  if (def.cumulative) {
    const pts = list.map((_, i) => ({ x: PAD.left + band * (i + 0.5), y: yOf(cumulative[i]), value: cumulative[i] }))
    line = { path: smoothPath(pts), points: pts }
  }

  return {
    key: def.key,
    title: def.title,
    unit: def.unit,
    fmt: def.fmt,
    total,
    bars,
    line,
    band,
    ticks: [0, max / 2, max].map((v) => ({ v, y: yOf(v), label: tickLabel(v, def.prefix || '') })),
    note: def.note,
    budget: def.budget || 0,
  }
}

const barPanels = computed(() => [
  buildBarPanel({
    key: 'tokens', title: 'Tokens por paso', unit: 'tokens', get: (l) => l.total_tokens, fmt: fmtInt,
    cumulative: true, note: 'Barras: tokens de cada paso · línea: acumulado', budget: s.value.budget_total_tokens,
  }),
  buildBarPanel({
    key: 'costo', title: 'Costo por paso', unit: 'USD', get: (l) => l.cost_usd, fmt: fmtUsd, prefix: '$',
    note: `${fmtUsd(s.value.cost_per_1k_tokens_usd)} por 1K tokens`,
  }),
  buildBarPanel({
    key: 'co2', title: 'CO₂e (est.) por paso', unit: 'g', get: (l) => l.co2_g, fmt: fmtCo2,
    note: `Estimado: ${fmtInt(s.value.co2_g_per_kwh)} g CO₂e por kWh`,
  }),
])

// --- Torta: energía (estimada) por paso ------------------------------------
const PIE_C = 70
const PIE_R = 62
const polar = (angle, r) => [PIE_C + r * Math.sin(angle), PIE_C - r * Math.cos(angle)]

const energyPie = computed(() => {
  const list = steps.value
  const total = list.reduce((sum, st) => sum + st.energy_wh, 0)
  let angle = 0
  const slices = list.map((st) => {
    const share = total > 0 ? st.energy_wh / total : 0
    const a0 = angle
    const a1 = angle + share * Math.PI * 2
    angle = a1
    let path = ''
    if (share >= 0.9999) {
      path = `M ${PIE_C} ${PIE_C - PIE_R} A ${PIE_R} ${PIE_R} 0 1 1 ${PIE_C - 0.01} ${PIE_C - PIE_R} Z`
    } else if (share > 0) {
      const [x0, y0] = polar(a0, PIE_R)
      const [x1, y1] = polar(a1, PIE_R)
      path = `M ${PIE_C} ${PIE_C} L ${x0} ${y0} A ${PIE_R} ${PIE_R} 0 ${share > 0.5 ? 1 : 0} 1 ${x1} ${y1} Z`
    }
    const [lx, ly] = polar((a0 + a1) / 2, PIE_R * 0.62)
    return {
      name: st.name,
      short: st.short,
      color: st.color,
      value: st.energy_wh,
      pct: Math.round(share * 100),
      path,
      lx,
      ly,
      showLabel: share >= 0.07,
    }
  })
  return { slices, total }
})

// --- Medidores con aguja ----------------------------------------------------
const G_CX = 100
const G_CY = 92
const G_R = 70
const gPoint = (p, r) => [G_CX - r * Math.cos(Math.PI * p), G_CY - r * Math.sin(Math.PI * p)]

function buildGauge(def) {
  const p = Math.min(1, Math.max(0, def.pct / 100))
  const [ex, ey] = gPoint(p, G_R)
  const [nx, ny] = gPoint(p, G_R - 6)
  return {
    ...def,
    track: `M ${G_CX - G_R} ${G_CY} A ${G_R} ${G_R} 0 0 1 ${G_CX + G_R} ${G_CY}`,
    fill: p > 0 ? `M ${G_CX - G_R} ${G_CY} A ${G_R} ${G_R} 0 0 1 ${ex} ${ey}` : '',
    needle: { x: nx, y: ny },
  }
}

const gauges = computed(() => {
  const verified = props.verification?.verified || 0
  const discarded = props.verification?.discarded || 0
  const evaluated = verified + discarded
  return [
    buildGauge({
      key: 'verif',
      title: 'Tasa de verificación',
      pct: evaluated > 0 ? Math.round((verified / evaluated) * 100) : 0,
      color: 'var(--color-verdeEsm)',
      sub: evaluated > 0 ? `${verified} de ${evaluated} afirmaciones verificadas` : 'sin afirmaciones evaluadas',
      note: 'Falsabilidad 3/3 (Loop 1)',
    }),
    buildGauge({
      key: 'poda',
      title: 'Poda del Loop 2',
      pct: Math.round(props.pruningPercent || 0),
      color: 'var(--color-oro)',
      sub: 'menos palabras que el borrador lógico',
      note: 'Freno de mano (eco-eficiencia)',
    }),
  ]
})

// --- Lectura al pasar el mouse / tocar (una por panel) ----------------------
const hover = ref(null) // { key, idx }
const isOn = (key, idx) => hover.value?.key === key && hover.value?.idx === idx
const isDim = (key, idx) => hover.value?.key === key && hover.value?.idx !== idx

function barReadout(panel) {
  if (hover.value?.key === panel.key) {
    const b = panel.bars[hover.value.idx]
    if (b) return `${b.name}: ${panel.fmt(b.value)} ${panel.unit} · ${b.pct}%`
  }
  return `Total ${panel.fmt(panel.total)} ${panel.unit}`
}
function pieReadout() {
  if (hover.value?.key === 'energia') {
    const sl = energyPie.value.slices[hover.value.idx]
    if (sl) return `${sl.name}: ${fmtDec(sl.value)} Wh · ${sl.pct}%`
  }
  return `Total ${fmtDec(energyPie.value.total)} Wh`
}

const dataTable = computed(() => steps.value)
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:p-4">
    <header class="mb-3 flex flex-wrap items-center gap-2 px-1">
      <h4 class="text-sm font-bold text-azulCorp">Panel de KPI de sostenibilidad</h4>
      <span class="rounded-full bg-oro/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-oroOscuro">ODS 12</span>
      <span class="rounded-full bg-verdeEsm/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-verdeEsm">ODS 13</span>

      <div class="ml-auto flex flex-wrap items-center gap-x-3 gap-y-1">
        <span v-for="st in steps" :key="`lg-${st.name}`" class="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span class="h-2.5 w-2.5 shrink-0 rounded-sm" :style="{ backgroundColor: st.color }"></span>{{ st.name }}
        </span>
      </div>
    </header>

    <!-- Panel único con celdas separadas por líneas finas, como el panel de
    referencia: 2 columnas en pantallas medianas, 1 en mobile. -->
    <div class="grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-2">
      <!-- Barras por paso: tokens (con línea acumulada), costo y CO2e -->
      <div v-for="panel in barPanels" :key="panel.key" class="min-w-0 bg-white p-3">
        <div class="flex flex-wrap items-baseline justify-between gap-x-2">
          <h5 class="text-[13px] font-bold text-azulCorp">{{ panel.title }}</h5>
          <span class="text-[11px] font-semibold text-slate-600">{{ barReadout(panel) }}</span>
        </div>
        <div class="text-[10px] text-slate-400">{{ panel.note }}</div>

        <svg :viewBox="`0 0 ${BW} ${BH}`" class="mt-1 h-auto w-full" role="img"
          :aria-label="`${panel.title}: ${panel.bars.map((b) => `${b.name} ${panel.fmt(b.value)} ${panel.unit}`).join(', ')}`">
          <template v-for="tick in panel.ticks" :key="tick.v">
            <line :x1="PAD.left" :x2="BW - PAD.right" :y1="tick.y" :y2="tick.y" stroke="#e2e8f0" stroke-width="1" />
            <text :x="PAD.left - 6" :y="tick.y + 3" text-anchor="end" font-size="9" fill="#64748b">{{ tick.label }}</text>
          </template>

          <path
            v-for="(b, i) in panel.bars"
            :key="`bar-${b.name}`"
            :d="b.path"
            :fill="b.color"
            :opacity="isDim(panel.key, i) ? 0.35 : 1"
            class="transition-opacity duration-150"
          />

          <template v-if="panel.line">
            <path :d="panel.line.path" fill="none" stroke="#0f172a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <circle
              v-for="(p, i) in panel.line.points"
              :key="`pt-${i}`"
              :cx="p.x"
              :cy="p.y"
              r="4"
              fill="#0f172a"
              stroke="#fff"
              stroke-width="2"
            />
          </template>

          <g v-for="(b, i) in panel.bars" :key="`xl-${b.name}`">
            <text :x="b.cx" :y="BH - 21" text-anchor="middle" font-size="9.5" fill="#64748b">{{ b.short }}</text>
            <text :x="b.cx" :y="BH - 8" text-anchor="middle" font-size="10" font-weight="700" fill="#0f172a">{{ panel.fmt(b.value) }}</text>
            <rect
              :x="b.bandX"
              :y="PAD.top"
              :width="panel.band"
              :height="BH - PAD.top"
              fill="transparent"
              class="cursor-pointer"
              @mouseenter="hover = { key: panel.key, idx: i }"
              @mouseleave="hover = null"
              @click="hover = isOn(panel.key, i) ? null : { key: panel.key, idx: i }"
            />
          </g>
        </svg>

        <div
          v-if="panel.budget"
          class="inline-block rounded-full px-2 py-0.5 text-[10px] font-bold"
          :class="overBudget(panel.total, panel.budget) ? 'bg-oro/15 text-oroOscuro' : 'bg-verdeEsm/15 text-verdeEsm'"
        >
          {{ overBudget(panel.total, panel.budget) ? `${fmtDec(ratio(panel.total, panel.budget), 1)}× el umbral del protocolo (${fmtInt(panel.budget)})` : 'dentro del umbral del protocolo' }}
        </div>
      </div>

      <!-- Torta: energía estimada por paso -->
      <div class="min-w-0 bg-white p-3">
        <div class="flex flex-wrap items-baseline justify-between gap-x-2">
          <h5 class="text-[13px] font-bold text-azulCorp">% de energía (est.) por paso</h5>
          <span class="text-[11px] font-semibold text-slate-600">{{ pieReadout() }}</span>
        </div>
        <div class="text-[10px] text-slate-400">{{ fmtDec(s.energy_wh_per_1k_tokens, 2) }} Wh por 1K tokens (estimado)</div>

        <div class="mt-2 flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
          <svg viewBox="0 0 140 140" class="h-36 w-36 shrink-0" role="img"
            :aria-label="`Energía por paso: ${energyPie.slices.map((sl) => `${sl.name} ${sl.pct}%`).join(', ')}`">
            <path
              v-for="(sl, i) in energyPie.slices"
              :key="`sl-${sl.name}`"
              :d="sl.path"
              :fill="sl.color"
              stroke="#fff"
              stroke-width="2"
              :opacity="isDim('energia', i) ? 0.35 : 1"
              class="cursor-pointer transition-opacity duration-150"
              @mouseenter="hover = { key: 'energia', idx: i }"
              @mouseleave="hover = null"
              @click="hover = isOn('energia', i) ? null : { key: 'energia', idx: i }"
            />
            <template v-for="sl in energyPie.slices" :key="`lb-${sl.name}`">
              <text v-if="sl.showLabel" :x="sl.lx" :y="sl.ly + 4" text-anchor="middle" font-size="12" font-weight="700" fill="#fff" class="pointer-events-none"
                style="paint-order: stroke; stroke: rgba(15,23,42,0.45); stroke-width: 2px;">{{ sl.pct }}%</text>
            </template>
          </svg>

          <ul class="space-y-1.5 text-[11px] text-slate-600">
            <li v-for="(sl, i) in energyPie.slices" :key="`li-${sl.name}`" class="flex items-center gap-2 rounded px-1"
              :class="isOn('energia', i) ? 'bg-slate-100' : ''"
              @mouseenter="hover = { key: 'energia', idx: i }" @mouseleave="hover = null">
              <span class="h-2.5 w-2.5 shrink-0 rounded-sm" :style="{ backgroundColor: sl.color }"></span>
              <span class="w-24">{{ sl.name }}</span>
              <span class="font-bold text-azulCorp">{{ fmtDec(sl.value) }} Wh</span>
              <span class="text-slate-400">{{ sl.pct }}%</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Medidores con aguja -->
      <div v-for="g in gauges" :key="g.key" class="min-w-0 bg-white p-3">
        <h5 class="text-[13px] font-bold text-azulCorp">{{ g.title }}</h5>
        <div class="text-[10px] text-slate-400">{{ g.note }}</div>

        <svg viewBox="0 0 200 118" class="mx-auto mt-1 h-auto w-full max-w-[16rem]" role="img" :aria-label="`${g.title}: ${g.pct}%, ${g.sub}`">
          <path :d="g.track" fill="none" stroke="var(--color-slate-200)" stroke-width="16" />
          <path v-if="g.fill" :d="g.fill" fill="none" :stroke="g.color" stroke-width="16" />
          <line :x1="G_CX" :y1="G_CY" :x2="g.needle.x" :y2="g.needle.y" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round" />
          <circle :cx="G_CX" :cy="G_CY" r="5" fill="#dc2626" stroke="#fff" stroke-width="2" />
          <text :x="G_CX - G_R" :y="G_CY + 14" text-anchor="middle" font-size="9" fill="#64748b">0</text>
          <text :x="G_CX + G_R" :y="G_CY + 14" text-anchor="middle" font-size="9" fill="#64748b">100</text>
          <text :x="G_CX" :y="G_CY + 27" text-anchor="middle" font-size="22" font-weight="800" font-style="italic" fill="#0f172a">{{ g.pct }}%</text>
        </svg>
        <div class="text-center text-[11px] text-slate-500">{{ g.sub }}</div>
      </div>
    </div>

    <!-- Vista de tabla: los mismos datos sin depender del color -->
    <details class="mt-3 rounded-xl border border-slate-100 bg-white px-4 py-2.5">
      <summary class="cursor-pointer text-[11px] font-semibold text-slate-500">Ver datos en tabla</summary>
      <div class="mt-2 overflow-x-auto">
        <table class="w-full min-w-[26rem] text-left text-[11px] text-slate-600">
          <thead>
            <tr class="border-b border-slate-100 text-[10px] uppercase tracking-wide text-slate-400">
              <th class="py-1 pr-3 font-semibold">Paso</th>
              <th class="py-1 pr-3 font-semibold">Entrada</th>
              <th class="py-1 pr-3 font-semibold">Salida</th>
              <th class="py-1 pr-3 font-semibold">Total</th>
              <th class="py-1 pr-3 font-semibold">Costo</th>
              <th class="py-1 pr-3 font-semibold">Energía (Wh)</th>
              <th class="py-1 font-semibold">CO₂e (g)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in dataTable" :key="`row-${l.name}`" class="border-b border-slate-50">
              <td class="py-1 pr-3 font-medium text-azulCorp">{{ l.name }}</td>
              <td class="py-1 pr-3">{{ fmtInt(l.prompt_tokens) }}</td>
              <td class="py-1 pr-3">{{ fmtInt(l.completion_tokens) }}</td>
              <td class="py-1 pr-3">{{ fmtInt(l.total_tokens) }}</td>
              <td class="py-1 pr-3">{{ fmtUsd(l.cost_usd) }}</td>
              <td class="py-1 pr-3">{{ fmtDec(l.energy_wh) }}</td>
              <td class="py-1">{{ fmtCo2(l.co2_g) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>

    <div class="mt-3 px-1 text-[10px] leading-relaxed text-slate-500">
      <strong class="font-semibold text-slate-600">Tokens y costo</strong> son medidos (los reporta la API del modelo).
      <strong class="font-semibold text-slate-600">Energía y CO₂e</strong> son estimaciones a partir de coeficientes de
      referencia, no una medición directa del proveedor. El umbral es el del protocolo AOPCCPS+IA. Pasa el mouse (o toca)
      una barra o porción para ver el detalle por paso.
    </div>
  </section>
</template>
