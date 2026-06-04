<script setup>
import AppNav from './components/layout/AppNav.vue'
import AppHeader from './components/layout/AppHeader.vue'
import EmulatorView from './views/EmulatorView.vue'
import RepositoryView from './views/RepositoryView.vue'
import HistoryView from './views/HistoryView.vue'
import { currentView } from './stores/appStore.js'
</script>

<template>
  <div class="flex h-screen flex-col bg-slate-950 text-slate-100">
    <AppHeader />
    <main class="flex flex-1 flex-col overflow-y-auto pb-16 lg:ml-64 lg:pb-0">
      <EmulatorView v-if="currentView === 'emulator'" />
      <RepositoryView v-else-if="currentView === 'repository'" />
      <HistoryView v-else-if="currentView === 'history'" />
    </main>
    <AppNav />
  </div>
</template>
