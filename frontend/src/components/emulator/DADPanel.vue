<script setup>
import { dadVariables } from '../../stores/appStore.js'
import DADMonitor from './DADMonitor.vue'
</script>

<template>
  <div class="grid grid-cols-5 gap-2 px-4 py-3">
    <DADMonitor
      v-for="(v, key) in dadVariables"
      :key="key"
      :label="v.label"
      :name="v.name"
      :status="v.status"
    />
  </div>
</template>
