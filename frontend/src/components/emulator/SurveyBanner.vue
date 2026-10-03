<script setup>
import { FEEDBACK_FORM_URL } from '../../constants.js'

defineEmits(['close'])
</script>

<template>
  <div
    class="relative rounded-3xl bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] p-[2px] shadow-[0_0_40px_rgba(212,175,55,0.45)]"
    role="region"
    aria-label="Invitación al cuestionario"
  >
    <div class="relative overflow-hidden rounded-[calc(1.5rem-2px)] bg-azulCorp px-4 py-4 sm:px-6 sm:py-5">
      <div class="pointer-events-none absolute -right-10 -top-12 h-40 w-40 rounded-full bg-oro/25 blur-3xl"></div>

      <button
        type="button"
        aria-label="Cerrar invitación"
        class="absolute right-3 top-3 z-10 flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
        @click="$emit('close')"
      ><span class="text-xl leading-none">×</span></button>

      <div class="relative flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:gap-5">
        <div class="flex min-w-0 flex-1 items-center gap-3 pr-7 sm:gap-5 sm:pr-0">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] text-azulCorp shadow-lg sm:h-14 sm:w-14">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6 sm:h-7 sm:w-7">
              <rect x="8" y="2" width="8" height="4" rx="1" />
              <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
              <path d="m9 14 2 2 4-4" />
            </svg>
          </div>

          <div class="min-w-0 flex-1">
            <div class="text-[10px] font-extrabold uppercase tracking-[0.25em] text-oro">Tu opinión cuenta</div>
            <div class="mt-0.5 text-base font-extrabold leading-tight text-white sm:text-xl">¿Nos ayudas a mejorar el simulador?</div>
            <div class="mt-1 hidden text-sm leading-relaxed text-slate-300 sm:block">Completa este breve cuestionario con tu experiencia; tarda menos de un minuto.</div>
          </div>
        </div>

        <a
          :href="FEEDBACK_FORM_URL"
          target="_blank"
          rel="noopener noreferrer"
          class="relative inline-flex w-full shrink-0 items-center justify-center sm:w-auto"
        >
          <span class="absolute -inset-1 animate-pulse rounded-2xl bg-oro/60 blur-md [animation-duration:1.8s]"></span>
          <span class="relative inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] px-6 py-3 text-sm font-extrabold text-azulCorp shadow-lg transition-transform hover:scale-105 active:scale-95">
            Completar cuestionario
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </span>
        </a>
      </div>
    </div>
  </div>
</template>
