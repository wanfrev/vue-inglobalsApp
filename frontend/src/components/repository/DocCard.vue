<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  date: String,
  category: String,
  sourceUrl: String
})

const badgeClass = computed(() => {
  const value = (props.category || '').toLowerCase()

  if (value.includes('gaceta') || value.includes('seniat') || value.includes('cv')) {
    return 'bg-amber-100 text-amber-800'
  }

  if (value.includes('nia') || value.includes('niif') || value.includes('ni')) {
    return 'bg-blue-100 text-blue-800'
  }

  if (value.includes('sostenibilidad') || value.includes('ven-ns 0')) {
    return 'bg-emerald-100 text-emerald-800'
  }

  return 'bg-slate-100 text-slate-700'
})
</script>

<template>
  <article
    class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:shadow-md"
  >
    <div class="mb-2 flex items-start justify-between gap-2">
      <h3 class="text-sm font-semibold text-slate-800">{{ title }}</h3>
      <span
        :class="badgeClass"
        class="shrink-0 rounded px-2 py-0.5 text-[10px] uppercase tracking-wider"
      >
        {{ category || 'General' }}
      </span>
    </div>
    <p class="mb-3 text-xs text-slate-500">Actualizado: {{ date || 'Sin fecha' }}</p>

    <a
      :href="sourceUrl || '#'"
      target="_blank"
      rel="noopener noreferrer"
      class="inline-flex rounded-lg border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100"
    >
      Ver fuente
    </a>
  </article>
</template>
