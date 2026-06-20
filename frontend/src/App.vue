<script setup>
import AppNav from './components/layout/AppNav.vue'
import AppHeader from './components/layout/AppHeader.vue'
import EmulatorView from './views/EmulatorView.vue'
import RepositoryView from './views/RepositoryView.vue'
import HistoryView from './views/HistoryView.vue'
import { currentView } from './stores/appStore.js'
</script>

<template>
  <div class="flex h-screen flex-col bg-gradient-to-b from-slate-50 via-white to-slate-100 text-azulCorp">
    <!-- Decorative background blobs (like the web) -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div class="absolute top-0 left-1/4 w-[420px] h-[420px] bg-violetaIA/15 rounded-full blur-[120px]"></div>
      <div class="absolute bottom-0 right-1/4 w-[480px] h-[480px] bg-oro/10 rounded-full blur-[130px]"></div>
      <div
        class="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:40px_40px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_40%,transparent_100%)] opacity-30"
      ></div>
    </div>

    <AppHeader />
    <main class="flex flex-1 flex-col overflow-y-auto pb-16 lg:ml-64 lg:pb-0">
      <EmulatorView v-if="currentView === 'emulator'" />
      <RepositoryView v-else-if="currentView === 'repository'" />
      <HistoryView v-else-if="currentView === 'history'" />
    </main>
    <AppNav />
  </div>
</template>
