<script setup>
import { onMounted, ref } from 'vue'
import { getHistory } from '../services/api.js'
import HistoryTable from '../components/history/HistoryTable.vue'
import ReportCard from '../components/history/ReportCard.vue'

const selected = ref(null)
const entries = ref([])
const isLoading = ref(false)
const loadError = ref('')

const ENTITY_LABELS = { publica: 'Pública', privada: 'Privada', mixta: 'Mixta' }

function mapRecord(record) {
  return {
    id: record.expediente_id,
    date: record.created_at ? new Date(record.created_at).toLocaleDateString() : '',
    entity: ENTITY_LABELS[record.entity_type] || record.entity_type,
    request: record.prompt,
    percent: record.compliance_score,
    cvStatus: record.criteria_cv,
    cvFailed: record.criteria_cv === 'failed',
    record,
  }
}

async function loadHistory() {
  isLoading.value = true
  loadError.value = ''
  try {
    const records = await getHistory({ limit: 100 })
    entries.value = records.map(mapRecord)
  } catch (error) {
    loadError.value = `No se pudo cargar el historial: ${error.message}`
  } finally {
    isLoading.value = false
  }
}

onMounted(loadHistory)
</script>

<template>
  <section class="min-h-0 flex-1 space-y-4 overflow-y-auto py-3 sm:py-4">
    <div class="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-azulCorp sm:text-2xl">Historial</h1>
      </div>
      <button
        @click="loadHistory"
        :disabled="isLoading"
        title="Actualizar historial"
        aria-label="Actualizar historial"
        class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white/80 text-slate-600 shadow-sm transition-all hover:-translate-y-0.5 hover:border-oro/40 hover:text-oroOscuro hover:shadow-md disabled:opacity-50"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <path d="M20 11a8.1 8.1 0 0 0-14.8-3L3 11" />
          <path d="M3 5v6h6" />
          <path d="M4 13a8.1 8.1 0 0 0 14.8 3L21 13" />
          <path d="M21 19v-6h-6" />
        </svg>
      </button>
    </div>

    <p v-if="loadError" class="rounded-2xl border border-violetaIA/20 bg-violetaIA/5 px-4 py-3 text-sm font-medium text-violetaIA">{{ loadError }}</p>

    <section class="soft-panel overflow-hidden p-3 sm:p-4">
      <HistoryTable
        :entries="entries"
        @select="selected = $event"
      />
      <p v-if="!isLoading && !entries.length" class="mt-4 text-sm text-slate-500">
        Aún no hay simulaciones registradas.
      </p>
    </section>

    <section v-if="selected" class="soft-panel overflow-hidden p-3 sm:p-4">
      <ReportCard
        :entry="selected"
        @close="selected = null"
      />
    </section>
  </section>
</template>
