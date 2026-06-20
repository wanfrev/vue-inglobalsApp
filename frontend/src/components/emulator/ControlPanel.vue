<script setup>
import { entityType, framework, setEntityType, setFramework, resetDadVariables, simulationStatus } from '../../stores/appStore.js'

const lawOptions = ['NIA 230', 'VEN-NS 0', 'NIIF S1/S2']

function onEntityChange(e) {
  setEntityType(e.target.value)
}

function onFrameworkChange(e) {
  setFramework(e.target.value)
}

function simulate() {
  resetDadVariables()
  simulationStatus.value = 'processing'
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Entidad</label>
      <select
        :value="entityType"
        @change="onEntityChange"
        class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-azulCorp outline-none focus:border-oro transition-colors"
      >
        <option value="publica">Pública</option>
        <option value="privada">Privada</option>
        <option value="mixta">Mixta</option>
      </select>
    </div>

    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Marco Normativo</label>
      <select
        :value="framework"
        @change="onFrameworkChange"
        class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-azulCorp outline-none focus:border-oro transition-colors"
      >
        <option v-for="law in lawOptions" :key="law" :value="law">{{ law }}</option>
      </select>
    </div>

    <button
      @click="simulate"
      :disabled="simulationStatus === 'processing'"
      class="w-full rounded-xl bg-gradient-to-r from-[#996515] to-[#D4AF37] px-5 py-2.5 text-sm font-bold text-white shadow-md hover:shadow-lg hover:shadow-oro/20 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
    >
      {{ simulationStatus === 'processing' ? 'Procesando...' : 'Simular' }}
    </button>
  </div>
</template>
