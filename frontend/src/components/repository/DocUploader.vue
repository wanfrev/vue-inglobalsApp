<script setup>
import { ref } from 'vue'

const show = ref(false)
const fileName = ref('')
</script>

<template>
  <button
    @click="show = true"
    class="fixed bottom-20 right-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-navy-600 text-white shadow-lg transition-colors hover:bg-navy-500 lg:bottom-6"
  >
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6">
      <path d="M12 5v14M5 12h14" />
    </svg>
  </button>

  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
    @click.self="show = false"
  >
    <div class="w-full max-w-sm rounded-lg border border-slate-700 bg-slate-900 p-6">
      <h2 class="mb-4 text-base font-semibold text-slate-100">Cargar Documento</h2>
      <label class="mb-3 flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed border-slate-600 p-6 text-sm text-slate-400 hover:border-navy-500">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="h-8 w-8">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
        </svg>
        <span>{{ fileName || 'Seleccionar archivo PDF' }}</span>
        <input type="file" accept=".pdf" class="hidden" @change="fileName = $event.target.files[0]?.name || ''" />
      </label>
      <div class="flex justify-end gap-2">
        <button @click="show = false" class="rounded px-3 py-1.5 text-sm text-slate-400 hover:text-slate-200">Cancelar</button>
        <button class="rounded bg-navy-600 px-4 py-1.5 text-sm text-white hover:bg-navy-500">Subir</button>
      </div>
    </div>
  </div>
</template>
