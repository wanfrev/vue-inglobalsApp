<script setup>
import { currentUser, logoutSession } from '../../stores/appStore.js'
</script>

<template>
  <header class="relative overflow-hidden bg-azulCorp text-white">
    <div class="absolute -right-24 -top-32 h-72 w-72 rounded-full bg-violetaIA/10 blur-3xl"></div>
    <div class="relative mx-auto flex w-full max-w-[1440px] items-center justify-between px-4 py-3 sm:px-6 sm:py-5 lg:px-10">
      <div class="flex min-w-0 items-center gap-3">
        <a href="https://inglobals.com" target="_blank" rel="noreferrer" class="group flex items-center gap-3">
        <img
          src="/logo.png"
          alt="Inglobals logo"
          class="h-8 w-auto transition-transform group-hover:scale-105"
        />
        <span class="text-lg font-bold tracking-tight text-white">
          Inglobal<span
            class="text-transparent bg-clip-text bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C]"
            >S</span
          >
        </span>
        </a>
      </div>

      <div class="flex items-center gap-2 sm:gap-3">
        <template v-if="currentUser">
          <span
            v-if="currentUser.is_paid"
            class="hidden rounded-full bg-verdeEsm/15 px-3 py-1.5 text-xs font-semibold text-verdeEsm sm:inline-flex"
          >
            Cuenta activa
          </span>
          <span
            v-else
            class="hidden rounded-full bg-oro/15 px-3 py-1.5 text-xs font-semibold text-oro sm:inline-flex"
          >
            {{ currentUser.free_queries_remaining }} de 3 consultas gratis
          </span>
          <button
            @click="logoutSession"
            title="Cerrar sesión"
            class="inline-flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-800/60 px-3 py-1.5 text-xs font-semibold text-slate-300 transition-colors hover:border-oro/40 hover:text-oro"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <path d="M16 17l5-5-5-5" />
              <path d="M21 12H9" />
            </svg>
            <span class="hidden sm:inline">Salir</span>
          </button>
        </template>
      </div>
    </div>
  </header>
</template>
