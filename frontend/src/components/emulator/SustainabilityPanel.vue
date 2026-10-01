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

// Por nombre, no por posición: el paso de reformulación de la consulta (ver
// engine.py) se agregó como primer ítem de "loops" y no tiene umbral propio
// del protocolo (solo Loop 1 y Loop 2 lo tienen, ver el White Paper).
const BUDGET_BY_LOOP_NAME = { 'Loop 1': 'budget_loop1_tokens', 'Loop 2': 'budget_loop2_tokens' }

const overBudget = (row) => row.budget > 0 && row.total > row.budget
const ratio = (row) => (row.budget > 0 ? row.total / row.budget : 0)

const maxCost = computed(() => Math.max(...loops.value.map((l) => l.cost_usd), 1e-9))
const maxEnergy = computed(() => Math.max(...loops.value.map((l) => l.energy_wh), 1e-9))

// --- Dona: distribución de tokens por paso ---------------------------------
// Orden categórico FIJO (nunca ciclado, ver skill de dataviz): mismos colores
// que ya usa el resto de la app para cada concepto, para no inventar una
// paleta nueva. Validado contra CVD con scripts/validate_palette.js.
const LOOP_COLOR_BY_NAME = {
  'Reformulación': 'var(--color-violetaIA)',
  'Loop 1': 'var(--color-oro)',
  'Loop 2': 'var(--color-verdeEsm)',
}
const RADIUS = 50
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
// "Surface gap" entre arcos adyacentes (ver marks-and-anatomy.md) — los
// separa sin necesidad de un borde que le agregue peso visual a algo que no
// es dato.
const SEGMENT_GAP = 3

const hoveredLoop = ref(null)

const donutSegments = computed(() => {
  const total = s.value.total_tokens || 0
  if (total <= 0) return []
  let cumulative = 0
  return loops.value.map((l) => {
    const share = l.total_tokens / total
    const rawLength = share * CIRCUMFERENCE
    const dash = Math.max(0, rawLength - SEGMENT_GAP)
    const segment = {
      name: l.name,
      total: l.total_tokens,
      pct: Math.round(share * 100),
      color: LOOP_COLOR_BY_NAME[l.name] || 'var(--color-azulCorp)',
      dasharray: `${dash} ${CIRCUMFERENCE - dash}`,
      dashoffset: -cumulative,
      budget: BUDGET_BY_LOOP_NAME[l.name] ? s.value[BUDGET_BY_LOOP_NAME[l.name]] : 0,
    }
    cumulative += rawLength
    return segment
  })
})

const activeSegment = computed(
  () => donutSegments.value.find((seg) => seg.name === hoveredLoop.value) || null
)
</script>

<template>
  <section class="rounded-2xl border border-verdeEsm/25 bg-verdeEsm/[0.04] p-4 sm:p-5">
    <header class="mb-4 flex flex-wrap items-center gap-2">
      <h4 class="text-sm font-bold text-azulCorp">Métricas / Reporte Sostenible</h4>
      <span class="rounded-full bg-oro/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-oroOscuro">ODS 12</span>
      <span class="rounded-full bg-verdeEsm/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-verdeEsm">ODS 13</span>
    </header>

    <!-- Tarjetas resumen -->
    <div class="grid grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
      <div class="min-w-0 rounded-xl border border-slate-200/80 bg-white p-3">
        <div class="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Tokens</div>
        <div class="mt-1 break-words text-lg font-bold text-azulCorp">{{ fmtInt(s.total_tokens) }}</div>
        <div class="mt-0.5 text-[10px] leading-snug text-slate-500">
          entrada {{ fmtInt(s.prompt_tokens) }} · salida {{ fmtInt(s.completion_tokens) }}
        </div>
      </div>
      <div class="min-w-0 rounded-xl border border-slate-200/80 bg-white p-3">
        <div class="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Costo</div>
        <div class="mt-1 break-words text-lg font-bold text-azulCorp">{{ fmtUsd(s.cost_usd) }}</div>
        <div class="mt-0.5 text-[10px] leading-snug text-slate-500">{{ fmtUsd(s.cost_per_1k_tokens_usd) }} por 1K tokens</div>
      </div>
      <div class="min-w-0 rounded-xl border border-slate-200/80 bg-white p-3">
        <div class="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Energía (est.)</div>
        <div class="mt-1 break-words text-lg font-bold text-azulCorp">{{ fmtDec(s.energy_wh) }} <span class="text-xs font-semibold text-slate-500">Wh</span></div>
        <div class="mt-0.5 text-[10px] leading-snug text-slate-500">{{ fmtDec(s.energy_wh_per_1k_tokens, 2) }} Wh por 1K tokens</div>
      </div>
      <div class="min-w-0 rounded-xl border border-slate-200/80 bg-white p-3">
        <div class="text-[10px] font-semibold uppercase tracking-wide text-slate-500">CO₂e (est.)</div>
        <div class="mt-1 break-words text-lg font-bold text-azulCorp">{{ fmtDec(s.co2_g, s.co2_g < 1 ? 3 : 2) }} <span class="text-xs font-semibold text-slate-500">g</span></div>
        <div class="mt-0.5 text-[10px] leading-snug text-slate-500">{{ fmtInt(s.co2_g_per_kwh) }} g por kWh</div>
      </div>
    </div>

    <!-- Gráfica: distribución de tokens por paso (dona) -->
    <div class="mt-5">
      <h5 class="mb-3 text-xs font-bold text-azulCorp">Distribución de tokens por paso</h5>
      <div class="flex flex-col items-center gap-4 sm:flex-row sm:items-center sm:gap-6">
        <div class="relative h-36 w-36 shrink-0">
          <svg viewBox="0 0 120 120" class="h-full w-full -rotate-90" role="img" aria-label="Distribución de tokens por paso de la consulta">
            <circle cx="60" cy="60" r="50" fill="none" stroke="var(--color-slate-200)" stroke-width="16" />
            <circle
              v-for="seg in donutSegments"
              :key="seg.name"
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke-width="16"
              stroke-linecap="butt"
              :stroke="seg.color"
              :stroke-dasharray="seg.dasharray"
              :stroke-dashoffset="seg.dashoffset"
              :opacity="hoveredLoop && hoveredLoop !== seg.name ? 0.35 : 1"
              class="cursor-pointer transition-opacity duration-150"
              @mouseenter="hoveredLoop = seg.name"
              @mouseleave="hoveredLoop = null"
            >
              <title>{{ seg.name }}: {{ fmtInt(seg.total) }} tokens ({{ seg.pct }}%)</title>
            </circle>
          </svg>
          <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
            <span class="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              {{ activeSegment ? activeSegment.name : 'Total' }}
            </span>
            <span class="text-xl font-bold text-azulCorp">
              {{ fmtInt(activeSegment ? activeSegment.total : s.total_tokens) }}
            </span>
            <span class="text-[10px] text-slate-500">
              tokens<template v-if="activeSegment"> · {{ activeSegment.pct }}%</template>
            </span>
          </div>
        </div>

        <!-- Leyenda: siempre presente con 2+ series, con valor y % directo (ver skill de dataviz) -->
        <div class="w-full space-y-1.5">
          <div
            v-for="seg in donutSegments"
            :key="`legend-${seg.name}`"
            class="flex flex-wrap items-center gap-x-2 gap-y-0.5 rounded-lg px-1.5 py-1 text-[11px] transition-colors"
            :class="hoveredLoop === seg.name ? 'bg-slate-100' : ''"
            @mouseenter="hoveredLoop = seg.name"
            @mouseleave="hoveredLoop = null"
          >
            <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ backgroundColor: seg.color }"></span>
            <span class="font-semibold text-slate-700">{{ seg.name }}</span>
            <span class="text-slate-500">{{ fmtInt(seg.total) }} tokens · {{ seg.pct }}%</span>
            <span
              v-if="seg.budget"
              class="ml-auto shrink-0 font-semibold"
              :class="overBudget(seg) ? 'text-oroOscuro' : 'text-verdeEsm'"
            >
              {{ overBudget(seg) ? `${fmtDec(ratio(seg), 1)}× el umbral` : 'dentro del umbral' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Gráfica: $ / consumo y energía por loop -->
    <div class="mt-5">
      <h5 class="mb-2 text-xs font-bold text-azulCorp">Costo y energía por loop</h5>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[20rem] text-left text-[11px]">
          <thead>
            <tr class="text-[10px] uppercase tracking-wide text-slate-500">
              <th class="pb-1.5 pr-3 font-semibold">Loop</th>
              <th class="pb-1.5 pr-3 font-semibold">Costo (USD)</th>
              <th class="pb-1.5 font-semibold">Energía est. (Wh)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in loops" :key="l.name" class="align-middle">
              <td class="py-1.5 pr-3 font-semibold text-slate-700">{{ l.name }}</td>
              <td class="py-1.5 pr-3">
                <div class="flex items-center gap-2">
                  <div class="h-2 w-16 shrink-0 overflow-hidden rounded-full bg-slate-200/70 sm:w-24">
                    <div class="h-full rounded-full bg-oro" :style="{ width: `${(l.cost_usd / maxCost) * 100}%` }"></div>
                  </div>
                  <span class="text-slate-600">{{ fmtUsd(l.cost_usd) }}</span>
                </div>
              </td>
              <td class="py-1.5">
                <div class="flex items-center gap-2">
                  <div class="h-2 w-16 shrink-0 overflow-hidden rounded-full bg-slate-200/70 sm:w-24">
                    <div class="h-full rounded-full bg-verdeEsm" :style="{ width: `${(l.energy_wh / maxEnergy) * 100}%` }"></div>
                  </div>
                  <span class="text-slate-600">{{ fmtDec(l.energy_wh) }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-4 text-[10px] leading-relaxed text-slate-500">
      <strong class="font-semibold text-slate-600">Tokens y costo</strong> son medidos (los reporta la API del modelo).
      <strong class="font-semibold text-slate-600">Energía y CO₂e</strong> son estimaciones a partir de coeficientes de
      referencia, no una medición directa del proveedor. El umbral es el del protocolo AOPCCPS+IA.
    </div>
  </section>
</template>
