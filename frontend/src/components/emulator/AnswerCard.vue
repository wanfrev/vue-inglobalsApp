<script setup>
import { computed } from 'vue'
import SustainabilityPanel from './SustainabilityPanel.vue'

const props = defineProps({
  result: { type: Object, required: true },
})

const ENTITY_LABELS = { publica: 'Pública', privada: 'Privada', mixta: 'Mixta' }

const loop1 = computed(() => props.result.loop1 || {})
const loop2 = computed(() => props.result.loop2 || {})
const entity = computed(() => ENTITY_LABELS[props.result.entity_type] || props.result.entity_type)

const consultedSources = computed(() => {
  const titles = (props.result.sources_used || []).map((s) => s.title)
  return [...new Set(titles)]
})

const pruningPercent = computed(() => Math.round((loop2.value.pruning_ratio || 0) * 100))
</script>

<template>
  <div class="space-y-3">
    <div
      v-if="loop1.loop1_passed === false"
      class="rounded-2xl border border-oro/40 bg-oro/5 px-4 py-3 text-xs font-medium text-oroOscuro"
    >
      El Loop 1 no pudo verificar información suficiente en la bibliografía documentada, así que la respuesta se limita a
      lo comprobable (falsabilidad 3/3).
    </div>

    <!-- Respuesta final (Loop 2) -->
    <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.05)] sm:p-5">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-oroOscuro">Respuesta</span>
        <span v-if="entity" class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
          Entidad: {{ entity }}
        </span>
        <span
          v-if="result.framework"
          class="max-w-full break-words rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600"
        >
          Marco: {{ result.framework }}
        </span>
      </div>

      <div class="break-words whitespace-pre-line text-sm leading-relaxed text-slate-800">{{ loop2.final_answer }}</div>

      <div class="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-slate-100 pt-3 text-[11px] text-slate-500">
        <span
          class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide"
          :class="loop2.condition_met ? 'bg-verdeEsm/15 text-verdeEsm' : 'bg-oro/15 text-oroOscuro'"
        >
          {{ loop2.condition_met ? 'Estado = verdadero' : 'Condición no cumplida' }}
        </span>
        <span>{{ loop2.words }} palabras<template v-if="loop2.max_words"> (máx. {{ loop2.max_words }})</template></span>
        <span v-if="loop2.draft_words && pruningPercent > 0">Poda: {{ pruningPercent }}% menos que el borrador lógico</span>
        <span v-if="result.expediente_id" class="ml-auto font-medium text-slate-400">{{ result.expediente_id }}</span>
      </div>
    </article>

    <!-- Trazabilidad del Loop 1 -->
    <details class="group rounded-2xl border border-slate-200 bg-slate-50/70 p-4 sm:p-5">
      <summary class="cursor-pointer list-none text-xs font-bold text-azulCorp">
        <span class="mr-1 inline-block text-slate-400 transition-transform group-open:rotate-90">▸</span>
        Trazabilidad del Loop 1 <span class="font-normal text-slate-500">— filtro filosófico, técnico y epistemológico</span>
      </summary>

      <div class="mt-4 space-y-4 text-xs leading-relaxed text-slate-700">
        <div v-if="loop1.ontological" class="grid gap-3 sm:grid-cols-2">
          <div>
            <div class="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">Ontológico</div>
            <div class="break-words">{{ loop1.ontological }}</div>
          </div>
          <div v-if="loop1.phenomenological">
            <div class="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">Fenomenológico</div>
            <div class="break-words">{{ loop1.phenomenological }}</div>
          </div>
        </div>

        <div v-if="loop1.verified_claims?.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-verdeEsm">Verificadas (falsabilidad 3/3)</div>
          <ul class="space-y-1.5">
            <li v-for="(c, i) in loop1.verified_claims" :key="`v${i}`" class="break-words">
              <span class="font-bold text-verdeEsm">✓</span> {{ c.claim }}
              <span v-if="c.source" class="italic text-slate-500">({{ c.source }})</span>
            </li>
          </ul>
        </div>

        <div v-if="loop1.discarded_claims?.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-violetaIA">Descartadas</div>
          <ul class="space-y-1.5">
            <li v-for="(c, i) in loop1.discarded_claims" :key="`d${i}`" class="break-words">
              <span class="font-bold text-violetaIA">✗</span> {{ c.claim }}
              <span v-if="c.reason" class="italic text-slate-500">— {{ c.reason }}</span>
            </li>
          </ul>
        </div>

        <div v-if="loop1.missing_info?.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-oroOscuro">Información faltante</div>
          <ul class="list-disc space-y-1 pl-4">
            <li v-for="(m, i) in loop1.missing_info" :key="`m${i}`" class="break-words">{{ m }}</li>
          </ul>
        </div>

        <div v-if="consultedSources.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">Bibliografía consultada</div>
          <div class="break-words text-slate-500">{{ consultedSources.join(' · ') }}</div>
        </div>
      </div>
    </details>

    <SustainabilityPanel v-if="result.sustainability" :sustainability="result.sustainability" />
  </div>
</template>
