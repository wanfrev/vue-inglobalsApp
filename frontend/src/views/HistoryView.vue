<script setup>
import { ref } from 'vue'
import { simulationHistory } from '../stores/appStore.js'
import HistoryTable from '../components/history/HistoryTable.vue'
import ReportCard from '../components/history/ReportCard.vue'

const selected = ref(null)

const sampleEntries = [
  {
    id: 'AUD-001',
    date: '12/05/2025',
    entity: 'Pública',
    request: 'Auditoría integral de estados financieros',
    percent: 100,
    cvFailed: false,
  },
  {
    id: 'AUD-002',
    date: '10/05/2025',
    entity: 'Privada',
    request: 'Revisión de cumplimiento tributario y SENIAT',
    percent: 60,
    cvFailed: true,
  },
  {
    id: 'AUD-003',
    date: '06/05/2025',
    entity: 'Mixta',
    request: 'Evaluación NIIF y certificación de trazabilidad documental',
    percent: 80,
    cvFailed: false,
  },
]

if (!simulationHistory.value.length) {
  simulationHistory.value.push(...sampleEntries)
}
</script>

<template>
  <div class="flex-1 space-y-5 overflow-y-auto bg-white/50 backdrop-blur-sm px-4 py-6 lg:px-8">
    <div class="mx-auto w-full max-w-7xl">
      <h2 class="text-lg font-semibold text-azulCorp">Historial y Memoria Técnica</h2>
      <p class="mt-1 text-sm text-slate-500">Evidencia de simulaciones y emisión de certificados legales de auditoría.</p>
    </div>

    <section class="mx-auto w-full max-w-7xl">
      <HistoryTable
        :entries="simulationHistory"
        @select="selected = $event"
      />
    </section>

    <section v-if="selected" class="mx-auto w-full max-w-7xl">
      <ReportCard
        :entry="selected"
        @close="selected = null"
      />
    </section>
  </div>
</template>
