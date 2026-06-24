<script setup>
import { ref } from 'vue'
import ControlPanel from '../components/emulator/ControlPanel.vue'
import SimulatorForm from '../components/emulator/SimulatorForm.vue'

const drawerOpen = ref(false)
</script>

<template>
  <div class="flex flex-1 lg:divide-x lg:divide-slate-200">

    <!-- Desktop: ControlPanel izquierdo -->
    <div class="hidden w-64 shrink-0 overflow-y-auto bg-white/60 backdrop-blur-sm p-4 lg:block">
      <ControlPanel />
    </div>

    <!-- Centro: SimulatorForm (prompt + DAD + resultados) -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Mobile config bar -->
      <div class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2 lg:hidden">
        <button
          @click="drawerOpen = true"
          class="flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 active:bg-slate-200"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
          Configurar
        </button>
      </div>
      <SimulatorForm />
    </div>

    <!-- Mobile Drawer -->
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
        </div>
      </div>
    </Teleport>
  </div>
</template>
