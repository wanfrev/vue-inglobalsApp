<script setup>
import DocCard from '../components/repository/DocCard.vue'
import DocUploader from '../components/repository/DocUploader.vue'
import { documents } from '../stores/appStore.js'

const categories = [
  { name: 'Venezolana', docs: [] },
  { name: 'Internacional', docs: [] },
  { name: 'Sostenibilidad', docs: [] },
]
</script>

<template>
  <div class="flex-1 space-y-6 overflow-y-auto px-4 py-6">
    <div class="flex items-center justify-between">
      <h2 class="text-base font-semibold text-slate-100">Repositorio Normativo</h2>
      <input
        type="text"
        placeholder="Buscar..."
        class="max-w-xs rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none placeholder:text-slate-500 focus:border-navy-500"
      />
    </div>

    <div v-for="cat in categories" :key="cat.name">
      <h3 class="mb-3 text-sm font-medium uppercase tracking-wider text-slate-500">{{ cat.name }}</h3>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <DocCard
          v-for="doc in cat.docs"
          :key="doc.title"
          :title="doc.title"
          :date="doc.date"
          :category="cat.name"
          :source-url="doc.sourceUrl"
        />
      </div>
      <p v-if="!cat.docs.length" class="text-sm text-slate-600">Sin documentos cargados aún.</p>
    </div>

    <DocUploader />
  </div>
</template>
