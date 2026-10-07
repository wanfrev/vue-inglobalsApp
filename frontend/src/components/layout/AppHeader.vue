<script setup>
import { sessionInfo } from '../../stores/appStore.js'
import SurveyButton from './SurveyButton.vue'

// BASE_URL (ver vite.config.js: base: '/simulador/') — un <img src="/logo.png">
// literal da 404 (Vite no reescribe strings, solo imports), estaba roto.
const logoUrl = `${import.meta.env.BASE_URL}logo.png`
</script>

<template>
  <header class="relative overflow-hidden bg-azulCorp text-white">
    <div class="absolute -right-24 -top-32 h-72 w-72 rounded-full bg-violetaIA/10 blur-3xl"></div>
    <div class="relative mx-auto flex w-full max-w-[1440px] items-center justify-between px-4 py-3 sm:px-6 sm:py-5 lg:px-10">
      <div class="flex min-w-0 shrink-0 items-center gap-3">
        <a href="https://inglobals.com" target="_blank" rel="noreferrer" class="group flex items-center gap-3">
        <img
          :src="logoUrl"
          alt="Inglobals logo"
          class="h-8 w-auto shrink-0 transition-transform group-hover:scale-105"
        />
        <span class="text-lg font-bold tracking-tight text-white">
          Inglobal<span
            class="text-transparent bg-clip-text bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C]"
            >S</span
          >
        </span>
        </a>
      </div>

      <!-- Sin límite de consultas (a pedido del cliente): ya no se muestra un
      contador de "consultas gratis restantes" — sería engañoso, porque no
      existe un tope contra el cual contar. Si una sesión quedó marcada como
      pagada (is_paid, ver database.py) igual se lo hacemos saber. -->
      <div class="flex min-w-0 items-center gap-2 sm:gap-3">
        <!-- Cuestionario: siempre disponible; deshabilitado al completarlo. -->
        <SurveyButton />
        <span
          v-if="sessionInfo?.is_paid"
          class="whitespace-nowrap rounded-full bg-verdeEsm/15 px-2.5 py-1.5 text-xs font-semibold text-verdeEsm sm:px-3"
        >
          Cuenta activa
        </span>
      </div>
    </div>
  </header>
</template>
