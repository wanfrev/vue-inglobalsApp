<script setup>
import { computed, ref } from 'vue'
import DocCard from '../components/repository/DocCard.vue'
import DocUploader from '../components/repository/DocUploader.vue'
import { documents } from '../stores/appStore.js'

const searchQuery = ref('')
const uploaderRef = ref(null)

const filteredDocuments = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  if (!query) {
    return documents.value
  }

  return documents.value.filter((doc) => {
    const title = (doc.title || '').toLowerCase()
    const category = (doc.category || '').toLowerCase()
    return title.includes(query) || category.includes(query)
  })
})

function openUploader() {
  uploaderRef.value?.openFilePicker()
}
</script>

<template>
  <div class="flex-1 space-y-6 overflow-y-auto bg-white/50 backdrop-blur-sm px-4 py-6 lg:px-8">
    <div class="mx-auto flex w-full max-w-7xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="relative w-full max-w-xl">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        >
          <path d="m21 21-4.34-4.34" />
          <circle cx="11" cy="11" r="8" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar ley, gaceta o normativa..."
          class="w-full max-w-xl rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm text-azulCorp outline-none transition-colors placeholder:text-slate-400 focus:border-oro"
        />
      </div>

      <button
        @click="openUploader"
        class="shrink-0 rounded-xl bg-gradient-to-r from-[#996515] to-[#D4AF37] px-5 py-2.5 text-sm font-bold text-white shadow-md hover:shadow-lg hover:shadow-oro/20 hover:-translate-y-0.5 transition-all"
      >
        Cargar Ley (PDF)
      </button>
    </div>

    <section class="mx-auto w-full max-w-7xl">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-azulCorp">Repositorio Normativo</h2>
        <p class="text-sm text-slate-500">{{ filteredDocuments.length }} documentos</p>
      </div>

      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <DocCard
          v-for="doc in filteredDocuments"
          :key="doc.title"
          :title="doc.title"
          :date="doc.date"
          :category="doc.category"
          :source-url="doc.sourceUrl"
        />
      </div>

      <p v-if="!filteredDocuments.length" class="mt-4 text-sm text-slate-500">
        Sin documentos cargados aún.
      </p>
    </section>

    <section class="mx-auto w-full max-w-7xl">
      <DocUploader ref="uploaderRef" />
    </section>
  </div>
</template>
