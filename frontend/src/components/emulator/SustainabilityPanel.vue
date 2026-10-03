<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  sustainability: { type: Object, required: true },
  // Afirmaciones del Loop 1: verificadas vs descartadas (falsabilidad 3/3).
  verification: { type: Object, default: () => ({ verified: 0, discarded: 0 }) },
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

// --- Estilo "dashboard" (a pedido del cliente, referencia tipo Mailgun) -----
// Tarjetas blancas sobre fondo gris muy claro, título chico a la izquierda,
// dona gruesa con la cifra grande al centro, y una línea suave con punto final.
//
// Dona por paso (Reformulación / Loop 1 / Loop 2): paleta categórica FIJA de
// marca (violeta, oro, verde), validada para fondo claro con
// scripts/validate_palette.js --mode light.
const STEP_COLOR = {
  'Reformulación': 'var(--color-violetaIA)',
  'Loop 1': 'var(--color-oro)',
  'Loop 2': 'var(--color-verdeEsm)',
}
const SHORT_STEP = { 'Reformulación': 'Reform.', 'Loop 1': 'L1', 'Loop 2': 'L2' }

const RADIUS = 50
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const RING_WIDTH = 15
const SEGMENT_GAP = 3

function buildRing(perStepValue) {
  const total = loops.value.reduce((sum, l) => sum + perStepValue(l), 0)
  let cumulative = 0
  return loops.value.map((l) => {
    const value = perStepValue(l)
    const share = total > 0 ? value / total : 0
    const rawLength = share * CIRCUMFERENCE
    const dash = Math.max(0, rawLength - SEGMENT_GAP)
    const segment = {
      name: l.name,
      shortName: SHORT_STEP[l.name] || l.name,
      value,
      pct: Math.round(share * 100),
      color: STEP_COLOR[l.name] || '#94a3b8',
      dasharray: `${dash} ${CIRCUMFERENCE - dash}`,
      dashoffset: -cumulative,
    }
    cumulative += rawLength
    return segment
  })
}

const metricCards = computed(() => [
  {
    key: 'tokens',
    label: 'Tokens',
    totalValue: s.value.total_tokens,
    fmt: fmtInt,
    unit: 'tokens',
    sub: `entrada ${fmtInt(s.value.prompt_tokens)} · salida ${fmtInt(s.value.completion_tokens)}`,
    segments: buildRing((l) => l.total_tokens),
    budget: s.value.budget_total_tokens,
  },
  {
    key: 'costo',
    label: 'Costo',
    totalValue: s.value.cost_usd,
    fmt: fmtUsd,
    unit: 'USD',
    sub: `${fmtUsd(s.value.cost_per_1k_tokens_usd)} por 1K tokens`,
    segments: buildRing((l) => l.cost_usd),
    budget: 0,
  },
  {
    key: 'energia',
    label: 'Energía (est.)',
    totalValue: s.value.energy_wh,
    fmt: (n) => fmtDec(n),
    unit: 'Wh',
    sub: `${fmtDec(s.value.energy_wh_per_1k_tokens, 2)} Wh por 1K tokens`,
    segments: buildRing((l) => l.energy_wh),
    budget: 0,
  },
  {
    key: 'co2',
    label: 'CO₂e (est.)',
    totalValue: s.value.co2_g,
    fmt: fmtCo2,
    unit: 'g CO₂e',
    sub: `${fmtInt(s.value.co2_g_per_kwh)} g por kWh`,
    segments: buildRing((l) => l.co2_g),
    budget: 0,
  },
])

// Un solo ref de hover para las 4 donas: { cardKey, loopName }.
const hovered = ref(null)
const isHovered = (cardKey, loopName) => hovered.value?.cardKey === cardKey && hovered.value?.loopName === loopName
const isDimmed = (cardKey, loopName) => hovered.value?.cardKey === cardKey && hovered.value?.loopName !== loopName

function hoveredSegment(card) {
  if (hovered.value?.cardKey !== card.key) return null
  return card.segments.find((seg) => seg.name === hovered.value.loopName) || null
}
const centerValue = (card) => {
  const seg = hoveredSegment(card)
  return card.fmt(seg ? seg.value : card.totalValue)
}
const centerPill = (card) => {
  const seg = hoveredSegment(card)
  return seg ? `${seg.shortName} · ${seg.pct}%` : card.unit
}

// La cifra central se achica según su largo para que nunca toque el anillo.
function centerSizeClass(text) {
  const len = String(text).length
  if (len <= 4) return 'text-[1.7rem]'
  if (len <= 6) return 'text-[1.3rem]'
  return 'text-[1.05rem]'
}

// --- Dona "Tasa de verificación" (afirmaciones verificadas / evaluadas) ------
const verificationStats = computed(() => {
  const verified = props.verification?.verified || 0
  const discarded = props.verification?.discarded || 0
  const total = verified + discarded
  const pct = total > 0 ? Math.round((verified / total) * 100) : 0
  const filled = total > 0 ? (verified / total) * CIRCUMFERENCE : 0
  const dash = filled >= CIRCUMFERENCE ? CIRCUMFERENCE : Math.max(0, filled - SEGMENT_GAP)
  return { verified, discarded, total, pct, dasharray: `${dash} ${CIRCUMFERENCE - dash}` }
})

// --- Línea "Estadísticas": tokens por paso ----------------------------------
// Series: Total / Entrada / Salida. Paleta validada para fondo claro
// (validate_palette.js --mode light: azul, coral, cian — todo PASS).
const LINE_SERIES = [
  { key: 'total_tokens', label: 'Total', color: '#2563eb' },
  { key: 'prompt_tokens', label: 'Entrada', color: '#e5484d' },
  { key: 'completion_tokens', label: 'Salida', color: '#0891b2' },
]
const W = 480
const H = 200
const PAD = { left: 46, right: 20, top: 16, bottom: 30 }
const plotW = W - PAD.left - PAD.right
const plotH = H - PAD.top - PAD.bottom

const yMax = computed(() => {
  const raw = Math.max(1, ...loops.value.flatMap((l) => LINE_SERIES.map((sr) => l[sr.key] || 0)))
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  return Math.ceil(raw / magnitude) * magnitude
})
const xAt = (i) => PAD.left + (loops.value.length > 1 ? (i / (loops.value.length - 1)) * plotW : plotW / 2)
const yAt = (v) => PAD.top + plotH - (v / yMax.value) * plotH
const yTicks = computed(() => [0, yMax.value / 2, yMax.value].map((v) => ({ v, y: yAt(v) })))

// Curva monótona (Fritsch–Carlson): suave, pero sin "rebotes" que sugieran
// valores intermedios que no existen.
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

const lineSeries = computed(() =>
  LINE_SERIES.map((sr) => {
    const points = loops.value.map((l, i) => ({ x: xAt(i), y: yAt(l[sr.key] || 0), value: l[sr.key] || 0 }))
    return { ...sr, points, path: smoothPath(points) }
  }),
)

const hoverStep = ref(null)
const tooltipLeftPct = computed(() =>
  hoverStep.value === null ? 0 : Math.min(78, Math.max(2, (xAt(hoverStep.value) / W) * 100 - 14)),
)
const fmtAxis = (v) => (v >= 1000 ? `${Number((v / 1000).toFixed(1))}K` : String(v))
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:p-4">
    <header class="mb-3 flex flex-wrap items-center gap-2 px-1">
      <h4 class="text-sm font-bold text-azulCorp">Métricas / Reporte Sostenible</h4>
      <span class="rounded-full bg-oro/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-oroOscuro">ODS 12</span>
      <span class="rounded-full bg-verdeEsm/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-verdeEsm">ODS 13</span>
    </header>

    <!-- Fila 1: línea "Estadísticas" + dona "Tasa de verificación" -->
    <div class="grid gap-3 lg:grid-cols-[minmax(0,1fr)_14.5rem]">
      <div class="min-w-0 rounded-xl border border-slate-100 bg-white p-4">
        <h5 class="text-sm font-semibold text-azulCorp">Estadísticas</h5>
        <div class="text-[11px] text-slate-500">Tokens por paso del protocolo</div>

        <div class="relative mt-2">
          <svg :viewBox="`0 0 ${W} ${H}`" class="h-auto w-full" role="img" aria-label="Tokens de entrada, salida y total en cada paso: reformulación, Loop 1 y Loop 2">
            <g>
              <template v-for="tick in yTicks" :key="tick.v">
                <line :x1="PAD.left" :x2="W - PAD.right" :y1="tick.y" :y2="tick.y" stroke="#e2e8f0" stroke-width="1" />
                <text :x="PAD.left - 8" :y="tick.y + 3.5" text-anchor="end" font-size="10" fill="#64748b">{{ fmtAxis(tick.v) }}</text>
              </template>
            </g>

            <text
              v-for="(l, i) in loops"
              :key="`x-${l.name}`"
              :x="xAt(i)"
              :y="H - 9"
              text-anchor="middle"
              font-size="10.5"
              fill="#64748b"
            >{{ l.name }}</text>

            <line
              v-if="hoverStep !== null"
              :x1="xAt(hoverStep)"
              :x2="xAt(hoverStep)"
              :y1="PAD.top"
              :y2="PAD.top + plotH"
              stroke="#cbd5e1"
              stroke-width="1"
            />

            <path
              v-for="sr in lineSeries"
              :key="sr.key"
              :d="sr.path"
              fill="none"
              :stroke="sr.color"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <template v-for="sr in lineSeries" :key="`dots-${sr.key}`">
              <circle
                v-for="(p, i) in sr.points"
                v-show="i === sr.points.length - 1 || i === hoverStep"
                :key="`${sr.key}-${i}`"
                :cx="p.x"
                :cy="p.y"
                r="4.5"
                :fill="sr.color"
                stroke="#fff"
                stroke-width="2"
              />
            </template>

            <rect
              v-for="(l, i) in loops"
              :key="`hit-${l.name}`"
              :x="xAt(i) - plotW / (2 * Math.max(1, loops.length - 1))"
              :y="PAD.top"
              :width="plotW / Math.max(1, loops.length - 1)"
              :height="plotH + 14"
              fill="transparent"
              class="cursor-pointer"
              @mouseenter="hoverStep = i"
              @mouseleave="hoverStep = null"
              @click="hoverStep = hoverStep === i ? null : i"
            />
          </svg>

          <div
            v-if="hoverStep !== null"
            class="pointer-events-none absolute top-1 z-10 min-w-[8.5rem] rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] shadow-md"
            :style="{ left: `${tooltipLeftPct}%` }"
          >
            <div class="mb-1 font-semibold text-azulCorp">{{ loops[hoverStep].name }}</div>
            <div v-for="sr in LINE_SERIES" :key="`tt-${sr.key}`" class="flex items-center justify-between gap-3 text-slate-600">
              <span class="flex items-center gap-1.5">
                <span class="h-2 w-2 rounded-full" :style="{ backgroundColor: sr.color }"></span>{{ sr.label }}
              </span>
              <span class="font-semibold text-azulCorp">{{ fmtInt(loops[hoverStep][sr.key]) }}</span>
            </div>
          </div>
        </div>

        <div class="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1">
          <span v-for="sr in LINE_SERIES" :key="`lg-${sr.key}`" class="flex items-center gap-1.5 text-[11px] text-slate-500">
            <span class="h-2 w-2 shrink-0 rounded-full" :style="{ backgroundColor: sr.color }"></span>{{ sr.label }}
          </span>
        </div>
      </div>

      <div class="flex flex-col rounded-xl border border-slate-100 bg-white p-4">
        <h5 class="text-sm font-semibold text-azulCorp">Tasa de verificación</h5>
        <div class="relative mx-auto mt-3 h-32 w-32 shrink-0">
          <svg viewBox="0 0 120 120" class="h-full w-full -rotate-90" role="img" :aria-label="`Tasa de verificación: ${verificationStats.pct}%, ${verificationStats.verified} afirmaciones verificadas de ${verificationStats.total}`">
            <circle cx="60" cy="60" r="50" fill="none" stroke="var(--color-slate-200)" :stroke-width="RING_WIDTH" />
            <circle
              v-if="verificationStats.total > 0"
              cx="60"
              cy="60"
              r="50"
              fill="none"
              :stroke-width="RING_WIDTH"
              stroke="var(--color-verdeEsm)"
              :stroke-dasharray="verificationStats.dasharray"
            >
              <title>{{ verificationStats.verified }} verificadas de {{ verificationStats.total }} evaluadas</title>
            </circle>
          </svg>
          <div class="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span class="text-[1.7rem] font-extrabold leading-none text-azulCorp">{{ verificationStats.pct }}<span class="ml-0.5 text-base font-bold">%</span></span>
          </div>
        </div>
        <div class="mx-auto mt-3 rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-500">
          {{ verificationStats.total ? `${verificationStats.verified} de ${verificationStats.total} afirmaciones` : 'sin afirmaciones evaluadas' }}
        </div>
        <div class="mt-2 text-center text-[10px] leading-snug text-slate-400">Falsabilidad 3/3 (Loop 1)</div>
      </div>
    </div>

    <!-- Fila 2: una dona por métrica, SIEMPRE las 4 visibles (2x2 en mobile) -->
    <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <div
        v-for="card in metricCards"
        :key="card.key"
        class="flex min-w-0 flex-col rounded-xl border border-slate-100 bg-white p-4"
      >
        <h5 class="text-sm font-semibold text-azulCorp">{{ card.label }}</h5>

        <div class="relative mx-auto mt-3 h-28 w-28 shrink-0 sm:h-[7.5rem] sm:w-[7.5rem]">
          <svg viewBox="0 0 120 120" class="h-full w-full -rotate-90" role="img" :aria-label="`${card.label}: ${card.fmt(card.totalValue)} ${card.unit}, por paso: ${card.segments.map((s2) => `${s2.name} ${s2.pct}%`).join(', ')}`">
            <circle cx="60" cy="60" r="50" fill="none" stroke="var(--color-slate-200)" :stroke-width="RING_WIDTH" />
            <circle
              v-for="seg in card.segments"
              :key="seg.name"
              cx="60"
              cy="60"
              r="50"
              fill="none"
              :stroke-width="RING_WIDTH"
              stroke-linecap="butt"
              :stroke="seg.color"
              :stroke-dasharray="seg.dasharray"
              :stroke-dashoffset="seg.dashoffset"
              :opacity="isDimmed(card.key, seg.name) ? 0.3 : 1"
              class="cursor-pointer transition-opacity duration-150"
              @mouseenter="hovered = { cardKey: card.key, loopName: seg.name }"
              @mouseleave="hovered = null"
              @click="hovered = isHovered(card.key, seg.name) ? null : { cardKey: card.key, loopName: seg.name }"
            >
              <title>{{ seg.name }}: {{ card.fmt(seg.value) }} {{ card.unit }} ({{ seg.pct }}%)</title>
            </circle>
          </svg>
          <div class="pointer-events-none absolute inset-0 flex items-center justify-center px-5 text-center">
            <span class="font-extrabold leading-none text-azulCorp" :class="centerSizeClass(centerValue(card))">{{ centerValue(card) }}</span>
          </div>
        </div>

        <div class="mx-auto mt-3 max-w-full truncate rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-500">
          {{ centerPill(card) }}
        </div>

        <div class="mt-2.5 flex flex-wrap items-center justify-center gap-x-2 gap-y-1">
          <span
            v-for="seg in card.segments"
            :key="`dot-${card.key}-${seg.name}`"
            class="flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium text-slate-500 transition-colors"
            :class="isHovered(card.key, seg.name) ? 'bg-slate-100 text-azulCorp' : ''"
            @mouseenter="hovered = { cardKey: card.key, loopName: seg.name }"
            @mouseleave="hovered = null"
          >
            <span class="h-2 w-2 shrink-0 rounded-full" :style="{ backgroundColor: seg.color }"></span>
            {{ seg.shortName }}
          </span>
        </div>

        <div v-if="card.sub" class="mt-2 text-center text-[10px] leading-snug text-slate-400">{{ card.sub }}</div>

        <div
          v-if="card.budget"
          class="mx-auto mt-2 rounded-full px-2 py-0.5 text-[10px] font-bold"
          :class="overBudget(card.totalValue, card.budget) ? 'bg-oro/15 text-oroOscuro' : 'bg-verdeEsm/15 text-verdeEsm'"
        >
          {{ overBudget(card.totalValue, card.budget) ? `${fmtDec(ratio(card.totalValue, card.budget), 1)}× el umbral` : 'dentro del umbral' }}
        </div>
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
            <tr v-for="l in loops" :key="`row-${l.name}`" class="border-b border-slate-50">
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
      el anillo, la leyenda o la línea para ver el detalle por paso.
    </div>
  </section>
</template>
