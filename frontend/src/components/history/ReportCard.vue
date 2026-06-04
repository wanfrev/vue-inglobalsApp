<script setup>
defineProps({
  entry: Object
})

defineEmits(['close'])
</script>

<template>
  <div class="rounded-lg border border-slate-700 bg-slate-800 p-5">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-100">Expediente #{{ entry?.id }}</h3>
      <button @click="$emit('close')" class="text-slate-500 hover:text-slate-300">✕</button>
    </div>
    <div class="space-y-1 text-sm text-slate-400">
      <p><span class="text-slate-500">Entidad:</span> {{ entry?.entity }}</p>
      <p><span class="text-slate-500">Fecha:</span> {{ entry?.date }}</p>
      <p><span class="text-slate-500">Solicitud:</span> {{ entry?.request }}</p>
    </div>
    <button
      class="mt-4 rounded bg-navy-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-navy-500"
    >
      Descargar Certificado DAD
    </button>
  </div>
</template>
