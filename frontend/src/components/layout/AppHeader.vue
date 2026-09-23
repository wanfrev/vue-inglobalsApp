<script setup>
import { sessionInfo } from '../../stores/appStore.js'
</script>

<template>
  <header class="relative overflow-hidden bg-azulCorp text-white">
    <div class="absolute -right-24 -top-32 h-72 w-72 rounded-full bg-violetaIA/10 blur-3xl"></div>
    <div class="relative mx-auto flex w-full max-w-[1440px] items-center justify-between px-4 py-3 sm:px-6 sm:py-5 lg:px-10">
      <div class="flex min-w-0 shrink-0 items-center gap-3">
        <a href="https://inglobals.com" target="_blank" rel="noreferrer" class="group flex items-center gap-3">
        <img
          src="/logo.png"
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

      <div class="flex min-w-0 items-center gap-2 sm:gap-3">
        <template v-if="sessionInfo">
          <span
            v-if="sessionInfo.is_paid"
            class="whitespace-nowrap rounded-full bg-verdeEsm/15 px-2.5 py-1.5 text-xs font-semibold text-verdeEsm sm:px-3"
          >
            Cuenta activa
          </span>
          <span
            v-else
            class="whitespace-nowrap rounded-full bg-oro/15 px-2.5 py-1.5 text-xs font-semibold text-oro sm:px-3"
          >
            <!-- Texto corto en pantallas muy angostas (<375px, ej. iPhone SE):
            "1 consultas gratis restantes" no cabe junto al logo y antes se
            encimaba con él. Tailwind v4 no trae un breakpoint "xs" por
            defecto, así que usamos un variant arbitrario. -->
            <span class="min-[375px]:hidden">{{ sessionInfo.free_queries_remaining }} gratis</span>
            <span class="hidden min-[375px]:inline">{{ sessionInfo.free_queries_remaining }} consultas gratis restantes</span>
          </span>
        </template>
      </div>
    </div>
  </header>
</template>
