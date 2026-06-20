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
    class="flex items-center justify-between border-b border-amber-200/20 bg-azulCorp/95 backdrop-blur-md px-4 py-3"
  >
    <div class="flex items-center gap-3">
      <a href="https://inglobals.com" target="_blank" class="flex items-center gap-3 group">
        <img
          src="/logo.png"
          alt="Inglobals logo"
          class="h-7 w-auto group-hover:scale-105 transition-transform"
        />
        <span class="text-lg font-bold text-white tracking-tight">
          Inglobal<span
            class="text-transparent bg-clip-text bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C]"
            >S</span
          >
        </span>
      </a>
      <span
        class="hidden text-[10px] font-semibold uppercase tracking-wider text-slate-400 sm:inline border-l border-slate-700 pl-3"
      >
        {{ title }}
      </span>
    </div>

    <div class="flex items-center gap-3 text-xs text-slate-400">
      <span class="hidden sm:inline">{{ entityLabel }}</span>
      <span
        v-if="activeLaws.length"
        class="hidden rounded-full bg-oro/20 px-2.5 py-0.5 text-[11px] text-oro md:inline font-medium"
      >
        {{ activeLaws.join(', ') }}
      </span>
    </div>
  </header>
</template>
