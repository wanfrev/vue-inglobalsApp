<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  sustainability: { type: Object, required: true },
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

// --- Tarjetas tipo "widget" (una dona por métrica) --------------------------
// A pedido del cliente: energía y CO2e también se grafican (antes eran solo
// números), y las 4 tarjetas comparten el mismo estilo oscuro con anillo que
// usan paneles de referencia tipo Mailgun/Stripe — fondo oscuro, cifra grande
// al centro, anillo de color por loop.
//
// Paleta categórica FIJA (nunca ciclada, ver skill de dataviz) — son "pasos
// oscuros" de los mismos colores de marca (oroOscuro, un verde esmeralda más
// oscuro, violetaIA), elegidos y validados específicamente para fondo oscuro
// con scripts/validate_palette.js --mode dark --surface "#0f172a" (el verde
// claro --color-verdeEsm y el oro --color-oro de la marca fallaban el banda
// de luminosidad en modo oscuro — por eso no son los mismos tonos que usan
// los badges ODS 12/13 de arriba, que sí están sobre fondo claro).
const DARK_LOOP_COLOR_BY_NAME = {
  'Reformulación': 'var(--color-violetaIA)',
  'Loop 1': 'var(--color-oroOscuro)',
  'Loop 2': '#059669',
}
const SHORT_LOOP_NAME = { 'Reformulación': 'Reform.', 'Loop 1': 'L1', 'Loop 2': 'L2' }

const RADIUS = 50
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
// "Surface gap" entre arcos adyacentes (ver marks-and-anatomy.md) — los separa
// sin un borde que le agregue peso visual a algo que no es dato.
const SEGMENT_GAP = 3

function buildRing(perLoopValue) {
  const total = loops.value.reduce((sum, l) => sum + perLoopValue(l), 0)
  let cumulative = 0
  return loops.value.map((l) => {
    const value = perLoopValue(l)
    const share = total > 0 ? value / total : 0
    const rawLength = share * CIRCUMFERENCE
    const dash = Math.max(0, rawLength - SEGMENT_GAP)
    const segment = {
      name: l.name,
      shortName: SHORT_LOOP_NAME[l.name] || l.name,
      value,
      pct: Math.round(share * 100),
      color: DARK_LOOP_COLOR_BY_NAME[l.name] || '#94a3b8',
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
    unit: '',
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
    unit: 'g',
    sub: `${fmtInt(s.value.co2_g_per_kwh)} g por kWh`,
    segments: buildRing((l) => l.co2_g),
    budget: 0,
  },
])

// { cardKey, loopName } del segmento bajo el mouse — un solo ref para las 4
// tarjetas, cada una revisa si el hover activo le pertenece.
const hovered = ref(null)
const isHovered = (cardKey, loopName) => hovered.value?.cardKey === cardKey && hovered.value?.loopName === loopName
const isDimmed = (cardKey, loopName) => hovered.value?.cardKey === cardKey && hovered.value?.loopName !== loopName

function centerValue(card) {
  if (hovered.value?.cardKey === card.key) {
    const seg = card.segments.find((s2) => s2.name === hovered.value.loopName)
    if (seg) return card.fmt(seg.value)
  }
  return card.fmt(card.totalValue)
}
function centerSub(card) {
  if (hovered.value?.cardKey === card.key) {
    const seg = card.segments.find((s2) => s2.name === hovered.value.loopName)
    if (seg) return `${seg.shortName} · ${seg.pct}%`
  }
  return card.unit
}
</script>

<template>
  <section class="rounded-2xl border border-verdeEsm/25 bg-verdeEsm/[0.04] p-4 sm:p-5">
    <header class="mb-4 flex flex-wrap items-center gap-2">
      <h4 class="text-sm font-bold text-azulCorp">Métricas / Reporte Sostenible</h4>
      <span class="rounded-full bg-oro/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-oroOscuro">ODS 12</span>
      <span class="rounded-full bg-verdeEsm/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-verdeEsm">ODS 13</span>
    </header>

    <!-- 4 tarjetas oscuras tipo widget, una dona por métrica -->
    <div class="grid grid-cols-2 gap-2.5 sm:grid-cols-4 sm:gap-3">
      <div
        v-for="card in metricCards"
        :key="card.key"
        class="flex min-w-0 flex-col items-center rounded-2xl bg-azulCorp px-3 py-4 text-center shadow-[0_8px_20px_rgba(15,23,42,0.25)]"
      >
        <div class="text-[10px] font-semibold uppercase tracking-wide text-white/55">{{ card.label }}</div>

        <div class="relative mx-auto mt-2.5 h-[5.5rem] w-[5.5rem] shrink-0 sm:h-24 sm:w-24">
          <svg viewBox="0 0 120 120" class="h-full w-full -rotate-90" role="img" :aria-label="`${card.label}: ${card.fmt(card.totalValue)} ${card.unit}, por paso: ${card.segments.map((s2) => `${s2.name} ${s2.pct}%`).join(', ')}`">
            <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="14" />
            <circle
              v-for="seg in card.segments"
              :key="seg.name"
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke-width="14"
              stroke-linecap="butt"
              :stroke="seg.color"
              :stroke-dasharray="seg.dasharray"
              :stroke-dashoffset="seg.dashoffset"
              :opacity="isDimmed(card.key, seg.name) ? 0.3 : 1"
              class="cursor-pointer transition-opacity duration-150"
              @mouseenter="hovered = { cardKey: card.key, loopName: seg.name }"
              @mouseleave="hovered = null"
            >
              <title>{{ seg.name }}: {{ card.fmt(seg.value) }} {{ card.unit }} ({{ seg.pct }}%)</title>
            </circle>
          </svg>
          <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
            <span class="break-all text-sm font-bold leading-tight text-white sm:text-base">{{ centerValue(card) }}</span>
            <span class="mt-0.5 text-[9px] text-white/50">{{ centerSub(card) }}</span>
          </div>
        </div>

        <!-- Leyenda compacta: siempre presente (ver skill de dataviz, "legend
        always present for >= 2 series") — nombre corto + punto de color;
        el detalle completo sale en el tooltip nativo al pasar el mouse. -->
        <div class="mt-3 flex flex-wrap items-center justify-center gap-x-2 gap-y-1">
          <span
            v-for="seg in card.segments"
            :key="`dot-${card.key}-${seg.name}`"
            class="flex items-center gap-1 rounded-full px-1 py-0.5 text-[9px] font-medium text-white/60 transition-colors"
            :class="isHovered(card.key, seg.name) ? 'bg-white/10 text-white' : ''"
            @mouseenter="hovered = { cardKey: card.key, loopName: seg.name }"
            @mouseleave="hovered = null"
          >
            <span class="h-1.5 w-1.5 shrink-0 rounded-full" :style="{ backgroundColor: seg.color }"></span>
            {{ seg.shortName }}
          </span>
        </div>

        <div v-if="card.sub" class="mt-2 text-[9px] leading-snug text-white/40">{{ card.sub }}</div>

        <!-- Umbral del protocolo: solo Tokens lo tiene definido (ver White Paper) -->
        <div
          v-if="card.budget"
          class="mt-1.5 rounded-full px-2 py-0.5 text-[9px] font-bold"
          :class="overBudget(card.totalValue, card.budget) ? 'bg-oro/20 text-oro' : 'bg-verdeEsm/20 text-verdeEsm'"
        >
          {{ overBudget(card.totalValue, card.budget) ? `${fmtDec(ratio(card.totalValue, card.budget), 1)}× el umbral` : 'dentro del umbral' }}
        </div>
      </div>
    </div>

    <div class="mt-4 text-[10px] leading-relaxed text-slate-500">
      <strong class="font-semibold text-slate-600">Tokens y costo</strong> son medidos (los reporta la API del modelo).
      <strong class="font-semibold text-slate-600">Energía y CO₂e</strong> son estimaciones a partir de coeficientes de
      referencia, no una medición directa del proveedor. El umbral es el del protocolo AOPCCPS+IA. Pasa el mouse (o toca)
      el anillo o la leyenda para ver el detalle por paso.
    </div>
  </section>
</template>
