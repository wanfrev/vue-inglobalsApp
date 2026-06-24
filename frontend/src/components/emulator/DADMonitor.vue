<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: String,
  name: String,
  status: { type: String, default: 'idle' },
  active: { type: Boolean, default: false }
})

const emit = defineEmits(['toggle'])

const cardClasses = computed(() => {
  if (!props.active) {
    return 'border-slate-200 bg-slate-50/80 text-slate-400 opacity-70'
  }
  switch (props.status) {
    case 'processing':
      return 'border-oro bg-oro/5 text-oro animate-pulse'
    case 'success':
      return 'border-verdeEsm bg-verdeEsm/5 text-verdeEsm'
    case 'error':
      return 'border-violetaIA bg-violetaIA/5 text-violetaIA'
    default:
      return 'border-oro bg-white text-azulCorp shadow-sm'
  }
})

const indicatorClass = computed(() => {
  if (!props.active) return 'bg-slate-300'
  switch (props.status) {
    case 'processing': return 'bg-oro animate-pulse'
    case 'success': return 'bg-verdeEsm'
    case 'error': return 'bg-violetaIA'
    default: return 'bg-oro'
  }
})
</script>

<template>
  <div
    @click="emit('toggle')"
    class="flex cursor-pointer items-center gap-3 rounded-xl border-2 px-4 py-3 transition-all duration-300 hover:scale-[1.01] active:scale-[0.99]"
    :class="cardClasses"
  >
    <span class="w-9 text-center text-xl font-black leading-none">{{ label }}</span>
    <span class="flex-1 text-xs leading-tight font-medium">{{ name }}</span>

    <!-- Status indicator -->
    <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors"
      :class="{
        'bg-slate-200 text-slate-400': !active,
        'bg-oro text-white': active && status === 'processing',
        'bg-verdeEsm text-white': active && status === 'success',
        'bg-violetaIA text-white': active && status === 'error',
        'bg-oro/20 text-oro': active && status === 'idle',
      }"
    >
      <template v-if="!active">
        ○
      </template>
      <template v-else-if="status === 'success'">
        ✓
      </template>
      <template v-else-if="status === 'error'">
        ✗
      </template>
      <template v-else-if="status === 'processing'">
        ⟳
      </template>
      <template v-else>
        ●
      </template>
    </span>
  </div>
</template>
