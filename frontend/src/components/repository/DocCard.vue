<script setup>
defineProps({
  title: String,
  date: String,
  category: String,
  sourceUrl: String
})
</script>

<template>
  <div class="rounded-lg border border-slate-700 bg-slate-800 p-4">
    <div class="mb-2 flex items-start justify-between gap-2">
      <h3 class="text-sm font-medium text-slate-200">{{ title }}</h3>
      <span
        class="shrink-0 rounded bg-slate-700 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-400"
      >
        {{ category }}
      </span>
    </div>
    <p class="mb-3 text-xs text-slate-500">Actualizado: {{ date }}</p>
    <button
      class="rounded border border-slate-600 px-3 py-1 text-xs text-slate-300 transition-colors hover:bg-slate-700"
    >
      Ver fuente
    </button>
  </div>
</template>
