<script setup>
import { computed } from 'vue'

defineEmits(['close'])

const props = defineProps({
  entry: Object
})

const complianceTone = computed(() => {
  const percent = Number(props.entry?.percent || 0)
  const isAlert = Boolean(props.entry?.cvFailed) || props.entry?.cvStatus === 'failed' || percent < 100
  return isAlert ? 'bg-oro/15 text-oroOscuro' : 'bg-verdeEsm/15 text-verdeEsm'
})
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-sm font-semibold text-azulCorp">Expediente #{{ entry?.id }}</h3>
      <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600">✕</button>
    </div>

    <div class="mb-4 flex items-center gap-3">
      <span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="complianceTone">
        {{ entry?.percent || 0 }}% {{ (entry?.cvFailed || entry?.cvStatus === 'failed' || (entry?.percent || 0) < 100) ? 'Alerta' : 'Aprobado' }}
      </span>
      <p class="text-xs text-slate-500">Resultado consolidado de cumplimiento normativo</p>
    </div>

    <div class="space-y-1 text-sm text-slate-600">
      <p><span class="text-slate-500">Entidad:</span> {{ entry?.entity }}</p>
      <p><span class="text-slate-500">Fecha:</span> {{ entry?.date }}</p>
      <p><span class="text-slate-500">Solicitud:</span> {{ entry?.request }}</p>
    </div>

    <button
      class="mt-4 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#996515] to-[#D4AF37] px-4 py-2 text-sm font-bold text-white shadow-md hover:shadow-lg hover:shadow-oro/20 hover:-translate-y-0.5 transition-all"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
        <path d="M12 12v6" />
        <path d="m9.5 15.5 2.5 2.5 2.5-2.5" />
      </svg>
      Descargar Certificado DAD
    </button>
  </div>
</template>
