<script setup>
import { ref } from 'vue'
import DADPanel from '../components/emulator/DADPanel.vue'
import ControlPanel from '../components/emulator/ControlPanel.vue'
import ChatFeed from '../components/emulator/ChatFeed.vue'

const drawerOpen = ref(false)
</script>

<template>
  <div class="flex flex-1 lg:divide-x lg:divide-slate-200">

    <!-- Desktop: ControlPanel izquierdo -->
    <div class="hidden w-64 shrink-0 overflow-y-auto bg-white/60 backdrop-blur-sm p-4 lg:block">
      <ControlPanel />
    </div>

    <!-- Chat centro (flex-1) -->
    <ChatFeed @open-drawer="drawerOpen = true" />

    <!-- Desktop: DADPanel derecho -->
    <div class="hidden w-72 shrink-0 overflow-y-auto bg-white/60 backdrop-blur-sm p-4 lg:block">
      <h3 class="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Ecuación DAD</h3>
      <DADPanel />
    </div>

    <!-- Mobile Drawer (panel deslizable) -->
    <Teleport to="body">
      <div
        v-if="drawerOpen"
        class="fixed inset-0 z-50 lg:hidden"
        @click.self="drawerOpen = false"
      >
        <div class="absolute inset-0 bg-black/50" />
        <div class="absolute bottom-0 left-0 right-0 max-h-[70vh] overflow-y-auto rounded-t-2xl bg-white px-5 pb-8 pt-5 shadow-xl">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-azulCorp">Configuración</h3>
            <button
              @click="drawerOpen = false"
              class="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
          <ControlPanel />
          <div class="mt-6">
            <h4 class="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Ecuación DAD</h4>
            <DADPanel />
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
