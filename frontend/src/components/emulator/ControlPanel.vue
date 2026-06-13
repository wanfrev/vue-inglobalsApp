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
        class="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-navy-500"
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
        class="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-navy-500"
      >
        <option v-for="law in lawOptions" :key="law" :value="law">{{ law }}</option>
      </select>
    </div>

    <button
      @click="simulate"
      :disabled="simulationStatus === 'processing'"
      class="w-full rounded-lg bg-navy-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-navy-500 active:bg-navy-700 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {{ simulationStatus === 'processing' ? 'Procesando...' : 'Simular' }}
    </button>
  </div>
</template>
