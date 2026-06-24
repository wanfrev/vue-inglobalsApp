<script setup>
import { dadVariables, toggleDadVariable } from '../../stores/appStore.js'
import DADMonitor from './DADMonitor.vue'
</script>

<template>
  <div class="flex flex-col gap-2">
    <DADMonitor
      v-for="(v, key) in dadVariables"
      :key="key"
      :label="v.label"
      :name="v.name"
      :status="v.status"
      :active="v.active"
      @toggle="toggleDadVariable(key)"
    />
  </div>
</template>
