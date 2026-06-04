<script setup>
import { ref } from 'vue'
import { simulationHistory } from '../stores/appStore.js'
import HistoryTable from '../components/history/HistoryTable.vue'
import ReportCard from '../components/history/ReportCard.vue'

const selected = ref(null)

const sampleEntries = [
  { id: 'AUD-001', date: '12/05/2025', entity: 'Pública', request: 'Auditoría de balance general', percent: 83 },
  { id: 'AUD-002', date: '10/05/2025', entity: 'Privada', request: 'Revisión de cumplimiento tributario', percent: 55 },
]

if (!simulationHistory.value.length) {
  simulationHistory.value.push(...sampleEntries)
}
</script>

<template>
  <div class="flex-1 space-y-4 overflow-y-auto px-4 py-6">
    <h2 class="text-base font-semibold text-slate-100">Historial y Memoria Técnica</h2>

    <HistoryTable
      :entries="simulationHistory"
      @select="selected = $event"
    />

    <ReportCard
      v-if="selected"
      :entry="selected"
      @close="selected = null"
    />
  </div>
</template>
