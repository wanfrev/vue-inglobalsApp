<script setup>
// Tarjeta del cuestionario del cliente: SIEMPRE visible en el chat, fija sobre el
// campo de texto. Es compacta (una sola fila, ~64 px en celular) para no
// empujar el campo de texto fuera de pantalla. Una vez completado el
// cuestionario queda en gris, deshabilitada.
import { FEEDBACK_FORM_URL } from '../../constants.js'
import { noteSurveyOpened, surveyCompleted } from '../../stores/appStore.js'
</script>

<template>
  <!-- Completado: tarjeta gris, sin enlace -->
  <div
    v-if="surveyCompleted"
    class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 sm:px-4"
    role="status"
  >
    <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-verdeEsm/15 text-verdeEsm">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
        <path d="M20 6 9 17l-5-5" />
      </svg>
    </div>
    <div class="min-w-0 flex-1 text-sm font-bold leading-tight text-slate-500">
      Cuestionario completado
      <span class="block text-xs font-normal">¡Gracias por tu opinión!</span>
    </div>
    <span class="shrink-0 cursor-not-allowed rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-400">Completado</span>
  </div>

  <!-- Pendiente: tarjeta dorada llamativa -->
  <div
    v-else
    class="rounded-2xl bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] p-[2px] shadow-[0_0_30px_rgba(212,175,55,0.4)]"
    role="region"
    aria-label="Cuestionario"
  >
    <div class="relative flex items-center gap-3 overflow-hidden rounded-[calc(1rem-2px)] bg-azulCorp px-3 py-2.5 sm:gap-4 sm:px-5 sm:py-3.5">
      <div class="pointer-events-none absolute -right-8 -top-10 h-32 w-32 rounded-full bg-oro/25 blur-3xl"></div>

      <div class="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] text-azulCorp shadow-lg sm:h-12 sm:w-12">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 sm:h-6 sm:w-6">
          <rect x="8" y="2" width="8" height="4" rx="1" />
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
          <path d="m9 14 2 2 4-4" />
        </svg>
      </div>

      <div class="relative min-w-0 flex-1">
        <div class="text-[9px] font-extrabold uppercase tracking-[0.2em] text-oro sm:text-[10px]">Tu opinión cuenta</div>
        <div class="text-sm font-extrabold leading-tight text-white sm:text-base">¿Nos ayudas a mejorar el simulador?</div>
        <div class="mt-0.5 hidden text-xs text-slate-300 sm:block">Responde este breve cuestionario; tarda menos de un minuto.</div>
      </div>

      <a
        :href="FEEDBACK_FORM_URL"
        target="_blank"
        rel="noopener noreferrer"
        class="relative shrink-0 rounded-xl bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] px-3 py-2 text-xs font-extrabold text-azulCorp shadow-lg transition-transform hover:scale-105 active:scale-95 sm:px-5 sm:py-2.5 sm:text-sm"
        @click="noteSurveyOpened"
      >
        Completar<span class="hidden sm:inline"> cuestionario</span> →
      </a>
    </div>
  </div>
</template>
