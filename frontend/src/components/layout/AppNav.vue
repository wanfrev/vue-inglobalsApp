<script setup>
import { currentView, setView } from '../../stores/appStore.js'

// BASE_URL (ver vite.config.js: base: '/simulador/') hay que anteponerlo a
// mano a los assets de /public referenciados como string — a diferencia de
// un <img src="./x.png"> importado, Vite NO reescribe un string literal
// "/x.png" en el build ni en dev. Sin esto, la imagen da 404 (ya pasaba con
// el logo del header, /logo.png — se corrigió también de paso).
const BASE = import.meta.env.BASE_URL

const views = [
  {
    id: 'emulator',
    label: 'Simulador Sostenible (IA)',
    // Logo IAaS que pidió el cliente (fondo quitado) en vez del ícono
    // genérico de líneas — ver iaas-logo.png en frontend/public.
    image: `${BASE}iaas-logo.png`,
  },
  {
    id: 'history',
    label: 'Historial',
    icon: 'M12 8v4l3 3M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z'
  }
]
</script>

<template>
  <div class="mx-auto w-full max-w-[1440px] px-4 pt-3 sm:px-6 sm:pt-4 lg:px-10">
    <nav class="flex items-center justify-center gap-4 rounded-2xl border border-slate-200/80 bg-white/75 p-1.5 shadow-[0_12px_30px_rgba(15,23,42,0.06)] backdrop-blur-xl">
      <div class="flex w-full min-w-0 items-center justify-center gap-1 sm:w-auto">
      <button
        v-for="view in views"
        :key="view.id"
        @click="setView(view.id)"
        class="group flex flex-1 items-center justify-center gap-2 rounded-xl px-2.5 py-2.5 text-sm font-semibold transition-all duration-200 sm:min-w-36 sm:flex-none sm:px-4"
        :class="
          currentView === view.id
            ? 'bg-gradient-to-r from-[#996515]/15 to-[#D4AF37]/10 text-oroOscuro shadow-[inset_0_1px_2px_rgba(255,255,255,0.8),0_3px_8px_rgba(15,23,42,0.06)]'
            : 'text-slate-500 hover:bg-slate-100 hover:text-azulCorp'
        "
      >
        <img
          v-if="view.image"
          :src="view.image"
          alt=""
          class="h-5 w-5 shrink-0 object-contain transition-transform group-hover:scale-105 sm:h-6 sm:w-6"
        />
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="h-4 w-4 shrink-0 transition-transform group-hover:scale-105 sm:h-[18px] sm:w-[18px]"
        >
          <path :d="view.icon" />
        </svg>
        {{ view.label }}
      </button>
      </div>
    </nav>
  </div>
</template>
