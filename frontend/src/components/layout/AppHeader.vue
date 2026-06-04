<script setup>
import { computed } from 'vue'
import { entityType, activeLaws, currentView } from '../../stores/appStore.js'

const viewTitles = {
  emulator: 'Emulador Virtual',
  repository: 'Repositorio Normativo',
  history: 'Historial de Expedientes',
}

const title = computed(() => viewTitles[currentView.value] || 'DAD')

const entityLabel = computed(() => {
  const labels = { publica: 'Pública', privada: 'Privada', mixta: 'Mixta' }
  return labels[entityType.value] || '—'
})
</script>

<template>
  <header
    class="flex items-center justify-between border-b border-slate-700 bg-slate-900 px-4 py-3"
  >
    <div class="flex items-center gap-3">
      <span
        class="hidden text-xs font-semibold uppercase tracking-wider text-slate-400 sm:inline"
      >
        DAD
      </span>
      <h1 class="text-sm font-semibold text-slate-100 sm:text-base">
        {{ title }}
      </h1>
    </div>

    <div class="flex items-center gap-3 text-xs text-slate-400">
      <span class="hidden sm:inline">{{ entityLabel }}</span>
      <span
        v-if="activeLaws.length"
        class="hidden rounded bg-navy-700 px-2 py-0.5 text-[11px] text-slate-300 md:inline"
      >
        {{ activeLaws.join(', ') }}
      </span>
    </div>
  </header>
</template>
