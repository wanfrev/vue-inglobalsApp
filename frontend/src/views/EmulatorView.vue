<script setup>
import DADPanel from '../components/emulator/DADPanel.vue'
import ControlPanel from '../components/emulator/ControlPanel.vue'
import ChatFeed from '../components/emulator/ChatFeed.vue'
</script>

<template>
  <div class="flex flex-1 flex-col">
    <DADPanel />
    <ControlPanel />
    <ChatFeed />
  </div>
</template>
