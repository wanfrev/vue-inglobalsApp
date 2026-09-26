<script setup>
import { ref } from 'vue'
import { exportSimulation } from '../../services/api.js'
import { sessionInfo } from '../../stores/appStore.js'
import AnswerCard from '../emulator/AnswerCard.vue'

defineEmits(['close'])

const props = defineProps({
  entry: Object
})

const isDownloading = ref(false)
const downloadError = ref('')

async function downloadCertificate() {
  isDownloading.value = true
  downloadError.value = ''
  try {
    const fullRecord = await exportSimulation(props.entry.id)
    const blob = new Blob([JSON.stringify(fullRecord, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `memoria-tecnica-${props.entry?.id || 'expediente'}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (error) {
    downloadError.value = error.message || 'No se pudo descargar'
  } finally {
    isDownloading.value = false
  }
}
</script>

<template>
  <div class="rounded-2xl border border-slate-200/80 bg-white/80 p-5 shadow-sm sm:p-6">
    <div class="mb-5 flex items-start justify-between gap-4">
      <div>
        <p class="text-[10px] font-bold uppercase tracking-[0.18em] text-oroOscuro">Detalle del expediente</p>
        <h3 class="mt-1 text-base font-bold text-azulCorp">Expediente #{{ entry?.id }}</h3>
      </div>
      <button @click="$emit('close')" aria-label="Cerrar detalle" class="flex h-8 w-8 items-center justify-center rounded-lg text-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600">×</button>
    </div>

    <div class="mb-5 grid gap-3 break-words text-sm text-slate-600 sm:grid-cols-2">
      <p><span class="text-slate-500">Fecha:</span> {{ entry?.date }}</p>
      <p><span class="text-slate-500">Entidad:</span> {{ entry?.entity }}</p>
      <p class="sm:col-span-2"><span class="text-slate-500">Consulta:</span> {{ entry?.request }}</p>
    </div>

    <AnswerCard v-if="entry?.result" :result="entry.result" />
    <p
      v-else
      class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600"
    >
      Este expediente se generó con el formato anterior (ecuación DAD) y no tiene el desglose por loops.
      Consumo registrado: {{ Number(entry?.tokens || 0).toLocaleString('es') }} tokens.
    </p>

    <button
      @click="downloadCertificate"
      :disabled="isDownloading"
      class="mt-5 inline-flex max-w-full items-center gap-2 rounded-xl bg-gradient-to-r from-[#996515] to-[#D4AF37] px-4 py-2 text-sm font-bold text-white shadow-md transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-oro/20 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
        <path d="M12 12v6" />
        <path d="m9.5 15.5 2.5 2.5 2.5-2.5" />
      </svg>
      {{ isDownloading ? 'Descargando...' : 'Descargar memoria técnica' }}
    </button>
    <p v-if="downloadError" class="mt-2 text-xs font-medium text-oroOscuro">{{ downloadError }}</p>
    <p v-if="!sessionInfo?.is_paid" class="mt-1 text-xs text-slate-400">Descargar requiere una cuenta activada.</p>
  </div>
</template>
