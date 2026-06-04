<script setup>
import { currentView, setView } from '../../stores/appStore.js'

const views = [
  {
    id: 'emulator',
    label: 'Emulador',
    icon: 'M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7M10 12h4'
  },
  {
    id: 'repository',
    label: 'Repositorio',
    icon: 'M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5A2.5 2.5 0 0 1 4 19.5ZM8 7h8M8 11h6'
  },
  {
    id: 'history',
    label: 'Historial',
    icon: 'M12 8v4l3 3M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z'
  }
]
</script>

<template>
  <!-- Desktop Sidebar -->
  <aside
    class="fixed left-0 top-0 z-40 hidden h-screen w-64 flex-col bg-slate-950 lg:flex"
  >
    <div class="flex items-center gap-2 border-b border-slate-800 px-6 py-5">
      <span class="text-sm font-bold uppercase tracking-widest text-slate-100">DAD</span>
    </div>
    <nav class="flex flex-col gap-1 px-3 pt-6">
      <button
        v-for="view in views"
        :key="view.id"
        @click="setView(view.id)"
        class="flex items-center gap-3 rounded-r-lg px-4 py-3 text-sm font-medium transition-all duration-150"
        :class="
          currentView === view.id
            ? 'border-l-2 border-navy-500 bg-slate-800 text-slate-100'
            : 'border-l-2 border-transparent text-slate-400 hover:bg-slate-800/50 hover:text-slate-300'
        "
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="h-5 w-5 shrink-0"
        >
          <path :d="view.icon" />
        </svg>
        {{ view.label }}
      </button>
    </nav>
  </aside>

  <!-- Mobile Bottom Navigation -->
  <nav
    class="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center justify-around border-t border-slate-200 bg-white shadow-lg lg:hidden"
  >
    <button
      v-for="view in views"
      :key="view.id"
      @click="setView(view.id)"
      class="flex flex-col items-center gap-0.5 px-3 py-1 transition-colors duration-150"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="h-6 w-6"
        :class="
          currentView === view.id ? 'text-navy-600' : 'text-slate-400'
        "
      >
        <path :d="view.icon" />
      </svg>
      <span
        class="text-[10px] font-medium"
        :class="
          currentView === view.id ? 'text-navy-600' : 'text-slate-500'
        "
      >
        {{ view.label }}
      </span>
    </button>
  </nav>
</template>
