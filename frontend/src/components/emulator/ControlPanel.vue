<script setup>
import { entityType, framework, setEntityType, setFramework } from '../../stores/appStore.js'

const lawOptions = ['NIA 230', 'VEN-NS 0', 'NIIF S1/S2']

function onEntityChange(e) {
  setEntityType(e.target.value)
}

function onFrameworkChange(e) {
  setFramework(e.target.value)
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Entidad</label>
      <select
        :value="entityType"
        @change="onEntityChange"
        class="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-azulCorp outline-none transition-colors focus:border-oro"
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
        class="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-azulCorp outline-none transition-colors focus:border-oro"
      >
        <option v-for="law in lawOptions" :key="law" :value="law">{{ law }}</option>
      </select>
    </div>
  </div>
</template>
