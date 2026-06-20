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
      'border-slate-200 bg-white text-slate-500': status === 'idle',
      'border-oro bg-oro/5 text-oro animate-pulse': status === 'processing',
      'border-verdeEsm bg-verdeEsm/10 text-verdeEsm': status === 'success',
      'border-violetaIA bg-violetaIA/10 text-violetaIA': status === 'error'
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
      class="ml-auto font-bold"
    >✓</span>
    <span
      v-else-if="status === 'error'"
      class="ml-auto font-bold"
    >✗</span>
  </div>
</template>
