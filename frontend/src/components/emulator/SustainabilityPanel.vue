<script setup>
import { computed } from 'vue'

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

// Una sola escala para todas las barras de tokens (Loop 1, Loop 2 y total), de
// modo que se comparen entre sí y contra el umbral del protocolo.
const scaleMax = computed(() => {
  const totals = loops.value.map((l) => l.total_tokens)
  return Math.max(s.value.total_tokens, s.value.budget_total_tokens, ...totals, 1) * 1.04
})
const pct = (value) => `${Math.min(100, (Number(value || 0) / scaleMax.value) * 100)}%`

const tokenRows = computed(() => {
  const rows = loops.value.map((l, i) => ({
    key: l.name,
    label: l.name,
    prompt: l.prompt_tokens,
    completion: l.completion_tokens,
    total: l.total_tokens,
    budget: i === 0 ? s.value.budget_loop1_tokens : s.value.budget_loop2_tokens,
  }))
  rows.push({
    key: 'total',
    label: 'Total',
    prompt: s.value.prompt_tokens,
    completion: s.value.completion_tokens,
    total: s.value.total_tokens,
    budget: s.value.budget_total_tokens,
  })
  return rows
})

const overBudget = (row) => row.budget > 0 && row.total > row.budget
const ratio = (row) => (row.budget > 0 ? row.total / row.budget : 0)

const maxCost = computed(() => Math.max(...loops.value.map((l) => l.cost_usd), 1e-9))
const maxEnergy = computed(() => Math.max(...loops.value.map((l) => l.energy_wh), 1e-9))
</script>

<template>
  <section class="rounded-2xl border border-verdeEsm/25 bg-verdeEsm/[0.04] p-4 sm:p-5">
    <header class="mb-4 flex flex-wrap items-center gap-2">
      <h4 class="text-sm font-bold text-azulCorp">Consumo de esta consulta</h4>
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

    <!-- Gráfica: tokens por loop vs umbral del protocolo -->
    <div class="mt-5">
      <h5 class="mb-2 text-xs font-bold text-azulCorp">Tokens por loop <span class="font-normal text-slate-500">— contra el umbral del protocolo</span></h5>
      <div class="space-y-2.5">
        <div
          v-for="row in tokenRows"
          :key="row.key"
          role="img"
          :aria-label="`${row.label}: ${fmtInt(row.total)} tokens (${fmtInt(row.prompt)} de entrada, ${fmtInt(row.completion)} de salida). Umbral: ${fmtInt(row.budget)}.`"
        >
          <div class="mb-1 flex items-baseline justify-between gap-2 text-[11px]">
            <span class="font-semibold text-slate-700">{{ row.label }}</span>
            <span class="text-right text-slate-500">
              {{ fmtInt(row.total) }} tokens
              <span v-if="row.budget" :class="overBudget(row) ? 'font-semibold text-oroOscuro' : 'font-semibold text-verdeEsm'">
                · {{ overBudget(row) ? `${fmtDec(ratio(row), 1)}× el umbral` : 'dentro del umbral' }}
              </span>
            </span>
          </div>
          <div class="relative h-3.5 w-full overflow-hidden rounded-full bg-slate-200/70">
            <div class="absolute inset-y-0 left-0 flex" :style="{ width: pct(row.total) }">
              <div class="h-full bg-azulCorp/70" :style="{ width: row.total ? `${(row.prompt / row.total) * 100}%` : '0%' }"></div>
              <div class="h-full flex-1 bg-oro"></div>
            </div>
            <div
              v-if="row.budget"
              class="absolute inset-y-0 w-0.5 bg-violetaIA"
              :style="{ left: pct(row.budget) }"
              :title="`Umbral: ${fmtInt(row.budget)} tokens`"
            ></div>
          </div>
        </div>
      </div>
      <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-slate-500">
        <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-sm bg-azulCorp/70"></span>Entrada (contexto)</span>
        <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-sm bg-oro"></span>Salida (incluye razonamiento interno)</span>
        <span class="inline-flex items-center gap-1"><span class="h-2 w-0.5 bg-violetaIA"></span>Umbral del protocolo</span>
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
