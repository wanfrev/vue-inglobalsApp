<script setup>
// Botón del cuestionario del cliente: SIEMPRE visible en la barra superior.
// Mientras no esté completado abre el formulario de Google; una vez completado
// queda deshabilitado ("Cuestionario completado").
//
// Google Forms no avisa a nuestra página cuando alguien envía el formulario,
// así que hay dos formas de saberlo:
//  1. Al volver de la pestaña del formulario se le pregunta "¿Ya lo completaste?"
//     (confirmación del propio usuario).
//  2. Automática: si en el mensaje de confirmación del formulario (Google Forms
//     > Configuración > Presentación) se agrega un enlace a
//     https://inglobals.com/simulador/?cuestionario=completado, al tocarlo la
//     app lo registra solo (ver appStore.js).
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { FEEDBACK_FORM_URL } from '../../constants.js'
import {
  dismissSurveyConfirmation,
  markSurveyCompleted,
  noteSurveyOpened,
  surveyAwaitingConfirmation,
  surveyCompleted,
} from '../../stores/appStore.js'

const askingConfirmation = ref(false)

// Al volver a esta pestaña tras abrir el formulario, se pide confirmar.
function onReturn() {
  if (document.visibilityState === 'visible' && surveyAwaitingConfirmation.value && !surveyCompleted.value) {
    askingConfirmation.value = true
  }
}

onMounted(() => {
  document.addEventListener('visibilitychange', onReturn)
  window.addEventListener('focus', onReturn)
})
onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', onReturn)
  window.removeEventListener('focus', onReturn)
})

function confirmCompleted() {
  markSurveyCompleted()
  askingConfirmation.value = false
}
function notYet() {
  dismissSurveyConfirmation()
  askingConfirmation.value = false
}
</script>

<template>
  <div class="relative">
    <button
      v-if="surveyCompleted"
      type="button"
      disabled
      aria-disabled="true"
      title="Gracias: ya completaste el cuestionario"
      class="inline-flex cursor-not-allowed items-center gap-1.5 whitespace-nowrap rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-bold text-slate-400 sm:px-4"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 text-verdeEsm">
        <path d="M20 6 9 17l-5-5" />
      </svg>
      <span class="hidden sm:inline">Cuestionario completado</span>
      <span class="sm:hidden">Completado</span>
    </button>

    <a
      v-else
      :href="FEEDBACK_FORM_URL"
      target="_blank"
      rel="noopener noreferrer"
      title="Responde el cuestionario (menos de un minuto)"
      class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] px-3 py-1.5 text-xs font-extrabold text-azulCorp shadow-[0_0_16px_rgba(212,175,55,0.4)] transition-transform hover:scale-105 active:scale-95 sm:px-4"
      @click="noteSurveyOpened"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
        <rect x="8" y="2" width="8" height="4" rx="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <path d="m9 14 2 2 4-4" />
      </svg>
      Cuestionario
    </a>

    <!-- Confirmación al volver del formulario -->
    <div
      v-if="askingConfirmation && !surveyCompleted"
      class="absolute right-0 top-full z-50 mt-2 w-64 rounded-xl border border-oro/40 bg-white p-3 text-azulCorp shadow-xl"
      role="dialog"
      aria-label="Confirmar cuestionario"
    >
      <div class="text-sm font-bold">¿Ya completaste el cuestionario?</div>
      <div class="mt-0.5 text-xs text-slate-500">Si lo enviaste, desactivamos el botón. ¡Gracias por tu opinión!</div>
      <div class="mt-2.5 flex gap-2">
        <button
          type="button"
          class="flex-1 rounded-lg bg-gradient-to-r from-[#996515] to-[#D4AF37] px-2 py-1.5 text-xs font-bold text-white hover:shadow-md"
          @click="confirmCompleted"
        >
          Sí, ya lo completé
        </button>
        <button
          type="button"
          class="flex-1 rounded-lg border border-slate-200 px-2 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          @click="notYet"
        >
          Todavía no
        </button>
      </div>
    </div>
  </div>
</template>
