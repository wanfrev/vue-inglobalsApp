<script setup>
defineProps({
  label: String,
  name: String,
  status: { type: String, default: 'idle' }
})
</script>

<template>
  <div
    class="flex flex-col items-center gap-1 rounded-lg border px-3 py-2 text-center transition-colors duration-300"
    :class="{
      'border-slate-700 bg-slate-800 text-slate-400': status === 'idle',
      'border-amber-500 bg-amber-900/30 text-amber-400 animate-pulse': status === 'processing',
      'border-emerald bg-emerald/10 text-emerald': status === 'success',
      'border-crimson bg-crimson/10 text-crimson': status === 'error'
    }"
  >
    <span class="text-lg font-bold leading-none">{{ label }}</span>
    <span class="text-[10px] leading-tight">{{ name }}</span>
  </div>
</template>
