<script setup>
import { ref } from 'vue'

const fileInput = ref(null)
const fileName = ref('')
const isDragging = ref(false)

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  fileName.value = event.target.files?.[0]?.name || ''
}

function handleDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  fileName.value = file?.name || ''
}

defineExpose({ openFilePicker })
</script>

<template>
  <div
    class="cursor-pointer rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-8 text-center transition-colors hover:border-oro/40 hover:bg-oro/5"
    @click="openFilePicker"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="mx-auto mb-3 h-10 w-10 text-slate-400"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="M7 10l5-5 5 5" />
      <path d="M12 5v12" />
    </svg>

    <p class="text-sm font-semibold text-azulCorp">Arrastra tu ley en PDF aquí o haz clic para seleccionar</p>
    <p class="mt-1 text-xs text-slate-500">Carga segura para indexación del repositorio normativo</p>
    <p v-if="fileName" class="mt-3 text-sm font-medium text-verdeEsm">Archivo seleccionado: {{ fileName }}</p>
    <p v-else-if="isDragging" class="mt-3 text-sm font-medium text-oro">Suelta el archivo para cargarlo</p>

    <input
      ref="fileInput"
      type="file"
      accept=".pdf,application/pdf"
      class="hidden"
      @change="handleFileChange"
    />
  </div>
</template>
