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

const record = computed(() => props.entry?.record || null)

function downloadCertificate() {
  const payload = record.value || props.entry
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `memoria-tecnica-${props.entry?.id || 'expediente'}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="rounded-2xl border border-slate-200/80 bg-white/80 p-5 shadow-sm sm:p-6">
    <div class="mb-5 flex items-start justify-between gap-4">
      <div>
        <p class="text-[10px] font-bold uppercase tracking-[0.18em] text-oroOscuro">Detalle de auditoría</p>
        <h3 class="mt-1 text-base font-bold text-azulCorp">Expediente #{{ entry?.id }}</h3>
      </div>
      <button @click="$emit('close')" aria-label="Cerrar detalle" class="flex h-8 w-8 items-center justify-center rounded-lg text-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600">×</button>
    </div>

    <div class="mb-5 flex flex-wrap items-center gap-3">
      <span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="complianceTone">
        {{ entry?.percent || 0 }}% {{ (entry?.cvFailed || entry?.cvStatus === 'failed' || (entry?.percent || 0) < 100) ? 'Alerta' : 'Aprobado' }}
      </span>
      <p class="text-xs text-slate-500">Resultado consolidado de cumplimiento normativo</p>
    </div>

    <div class="grid gap-3 break-words text-sm text-slate-600 sm:grid-cols-2">
      <p><span class="text-slate-500">Entidad:</span> {{ entry?.entity }}</p>
      <p v-if="record?.framework"><span class="text-slate-500">Marco normativo:</span> {{ record.framework }}</p>
      <p><span class="text-slate-500">Fecha:</span> {{ entry?.date }}</p>
      <p class="sm:col-span-2"><span class="text-slate-500">Solicitud:</span> {{ entry?.request }}</p>
      <template v-if="record">
        <p v-if="record.attached_files?.length" class="sm:col-span-2">
          <span class="text-slate-500">Archivos adjuntos:</span> {{ record.attached_files.join(', ') }}
        </p>
        <p v-if="record.corrective_action" class="sm:col-span-2"><span class="text-slate-500">Acción correctiva:</span> {{ record.corrective_action }}</p>
        <p v-if="record.question_well_formed === false" class="text-oroOscuro sm:col-span-2">
          <span class="text-slate-500">Nota:</span> {{ record.question_feedback }}
        </p>
        <p v-if="record.total_tokens" class="sm:col-span-2">
          <span class="text-slate-500">Costo IA:</span>
          {{ record.total_tokens }} tokens ≈ ${{ Number(record.estimated_cost_usd || 0).toFixed(6) }} USD
        </p>
      </template>
    </div>

    <button
      @click="downloadCertificate"
      class="mt-4 inline-flex max-w-full items-center gap-2 rounded-xl bg-gradient-to-r from-[#996515] to-[#D4AF37] px-4 py-2 text-sm font-bold text-white shadow-md transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-oro/20"
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
