<script setup>
defineProps({
  label: String,
  name: String,
  status: { type: String, default: 'idle' }
})
</script>

<template>
  <div
    class="flex items-center gap-3 rounded-lg border px-3 py-2.5 transition-colors duration-300"
    :class="{
      'border-slate-700 bg-slate-800 text-slate-400': status === 'idle',
      'border-amber-500 bg-amber-900/30 text-amber-400 animate-pulse': status === 'processing',
      'border-emerald bg-emerald/10 text-emerald': status === 'success',
      'border-crimson bg-crimson/10 text-crimson': status === 'error'
    }"
  >
    <span class="w-8 text-center text-lg font-bold leading-none">{{ label }}</span>
    <span class="text-xs leading-tight">{{ name }}</span>
    <span
      v-if="status === 'processing'"
      class="ml-auto text-[10px] uppercase tracking-wider opacity-70"
    >
      verificando...
    </span>
    <span
      v-else-if="status === 'success'"
      class="ml-auto"
    >✓</span>
    <span
      v-else-if="status === 'error'"
      class="ml-auto"
    >✗</span>
  </div>
</template>
