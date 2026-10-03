<script setup>
import { ref } from 'vue'
import { simulate, startSession } from '../../services/api.js'
import AnswerCard from './AnswerCard.vue'
import { promptText, setSession, simulationStatus, updateSessionStatus } from '../../stores/appStore.js'
import SurveyBanner from './SurveyBanner.vue'
import { SURVEY_AT_QUERY_NUMBERS } from '../../constants.js'

const messages = ref([])
const showSurvey = ref(false)
const isProcessing = ref(false)

// Adjuntar un archivo a la consulta (a pedido del cliente): la IA lo usa
// como fuente admisible además de la bibliografía, solo para ESTA consulta
// (no se indexa). Mismos límites que valida el backend (ver
// ATTACHMENT_MAX_FILE_SIZE_MB en config.py) — se replican acá para avisar
// de inmediato sin esperar el viaje al servidor.
const ATTACHMENT_ACCEPT = '.pdf,.docx,.txt'
const ATTACHMENT_MAX_BYTES = 8 * 1024 * 1024
const attachedFile = ref(null)
const attachmentError = ref('')
const fileInput = ref(null)

function canSimulate() {
  return promptText.value.trim().length > 0 && !isProcessing.value
}

function openFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(event) {
  const file = event.target.files?.[0]
  event.target.value = '' // permite volver a elegir el mismo archivo después de quitarlo
  if (!file) return

  attachmentError.value = ''
  const ext = `.${file.name.split('.').pop()?.toLowerCase() || ''}`
  if (!ATTACHMENT_ACCEPT.split(',').includes(ext)) {
    attachmentError.value = 'El adjunto debe ser PDF, Word (.docx) o texto (.txt).'
    return
  }
  if (file.size > ATTACHMENT_MAX_BYTES) {
    attachmentError.value = 'El archivo adjunto supera el límite de 8 MB.'
    return
  }
  attachedFile.value = file
}

function removeAttachment() {
  attachedFile.value = null
  attachmentError.value = ''
}

function fmtFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Si el token quedó inválido o nunca se guardó (ver el fix de getToken() en
// api.js), un 401 en pleno chat no debería mostrarle un error crudo al
// usuario: pedimos una sesión nueva y reintentamos la MISMA consulta una vez
// — igual que App.vue hace al cargar la página, pero también aquí en medio
// del chat.
async function simulateWithRetry(prompt, file) {
  try {
    return await simulate({ prompt, file })
  } catch (error) {
    if (error.status !== 401) throw error
    const session = await startSession()
    setSession(session)
    return await simulate({ prompt, file })
  }
}

async function send() {
  if (!canSimulate()) return

  const text = promptText.value
  const file = attachedFile.value

  isProcessing.value = true
  simulationStatus.value = 'processing'

  showSurvey.value = false
  messages.value.push({ role: 'user', text, fileName: file?.name || '' })
  promptText.value = ''
  attachedFile.value = null
  attachmentError.value = ''

  try {
    const result = await simulateWithRetry(text, file)

    updateSessionStatus(result)

    if (result.in_scope === false) {
      messages.value.push({
        role: 'alert',
        text: result.out_of_scope_reason || 'Esta pregunta está fuera del alcance de este sistema (auditoría, cumplimiento legal y contable en Venezuela).',
        failedVar: 'Fuera de contexto',
      })
      return
    }

    messages.value.push({ role: 'answer', result })

    // Cuestionario del cliente: se ofrece al llegar a la 3.ª y 4.ª consulta
    // válida de la sesión (free_queries_used ya incluye esta respuesta).
    showSurvey.value = SURVEY_AT_QUERY_NUMBERS.includes(result.free_queries_used)
  } catch (error) {
    messages.value.push({
      role: 'alert',
      text: `Error al procesar la solicitud: ${error.message}`,
    })
  } finally {
    isProcessing.value = false
    simulationStatus.value = 'idle'
  }
}
</script>

<template>
  <div class="soft-panel flex min-h-0 flex-1 flex-col overflow-hidden rounded-[28px]">
    <!-- Results / Messages Feed -->
    <div class="min-h-0 flex-1 space-y-4 overflow-y-auto bg-white/35 px-3 py-4 sm:px-8 sm:py-8">
      <div
        v-if="!messages.length"
        class="mx-auto flex max-w-xl flex-col items-center justify-center py-12 text-center sm:py-16"
      >
        <div class="mb-5 flex h-16 w-16 items-center justify-center rounded-[22px] bg-slate-100 text-slate-400 shadow-[inset_4px_4px_8px_rgba(15,23,42,0.08),inset_-4px_-4px_8px_rgba(255,255,255,0.95)]">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="h-7 w-7">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <path d="m7 10 5-5 5 5" />
            <path d="M12 5v12" />
          </svg>
        </div>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="mx-auto w-full max-w-4xl space-y-3"
      >
        <!-- Prompt enviado -->
        <div v-if="msg.role === 'user'" class="flex items-start gap-3 rounded-2xl border border-oro/20 bg-oro/5 p-4 shadow-sm">
          <span class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-oro/15 text-xs text-oroOscuro">01</span>
          <div class="min-w-0 flex-1 break-words">
            <p class="mb-1 text-[11px] font-semibold uppercase tracking-wider text-oroOscuro">Consulta</p>
            <p class="text-sm text-azulCorp leading-relaxed">{{ msg.text }}</p>
            <div v-if="msg.fileName" class="mt-2 inline-flex max-w-full items-center gap-1.5 rounded-lg border border-oro/30 bg-white/70 px-2 py-1 text-[11px] font-medium text-oroOscuro">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 shrink-0">
                <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
              <span class="truncate">{{ msg.fileName }}</span>
            </div>
          </div>
        </div>

        <!-- Respuesta del protocolo AOPCCPS+IA (Loop 1 + Loop 2 + consumo) -->
        <AnswerCard v-else-if="msg.role === 'answer'" :result="msg.result" />


        <!-- Alerta de rebote -->
        <div
          v-else-if="msg.role === 'alert'"
          class="rounded-2xl border border-violetaIA/15 border-l-4 border-l-violetaIA bg-violetaIA/5 p-4"
        >
          <div class="mb-1 flex items-center gap-2">
            <span class="text-sm font-bold text-violetaIA">Alerta de Rebote</span>
            <span
              v-if="msg.failedVar"
              class="rounded bg-violetaIA/20 px-1.5 py-0.5 text-[11px] font-semibold uppercase text-violetaIA"
            >
              {{ msg.failedVar }}
            </span>
          </div>
          <p class="break-words text-sm text-slate-700 whitespace-pre-line">{{ msg.text }}</p>
        </div>

      </div>

      <!-- Processing indicator -->
      <div v-if="isProcessing" class="mx-auto w-full max-w-4xl">
        <div class="inline-flex items-center gap-2 rounded-2xl rounded-tl-none border border-slate-200 bg-white px-4 py-2.5 shadow-sm">
          <div class="flex gap-1">
            <span class="h-2 w-2 animate-bounce rounded-full bg-oro [animation-delay:-0.3s]"></span>
            <span class="h-2 w-2 animate-bounce rounded-full bg-oro [animation-delay:-0.15s]"></span>
            <span class="h-2 w-2 animate-bounce rounded-full bg-oro"></span>
          </div>
          <span class="text-xs text-slate-500">Procesando solicitud...</span>
        </div>
      </div>
    </div>

    <!-- Compose area -->
    <div class="border-t border-slate-200/80 bg-white/80 px-3 py-3 backdrop-blur-md sm:px-8 sm:py-4">
      <div class="mx-auto w-full max-w-4xl">
        <!-- Cuestionario del cliente: fijo sobre el campo de texto (visible sin
        hacer scroll) en la 3.ª y 4.ª consulta; se puede cerrar. -->
        <SurveyBanner v-if="showSurvey" class="mb-3" @close="showSurvey = false" />
        <p v-if="attachmentError" class="mb-2 text-xs font-medium text-violetaIA">{{ attachmentError }}</p>

        <!-- Chip del archivo adjunto, antes de enviar -->
        <div v-if="attachedFile" class="mb-2 inline-flex max-w-full items-center gap-2 rounded-xl border border-oro/30 bg-oro/5 px-3 py-1.5 text-xs font-medium text-oroOscuro">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 shrink-0">
            <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
          <span class="truncate">{{ attachedFile.name }}</span>
          <span class="shrink-0 text-oroOscuro/60">{{ fmtFileSize(attachedFile.size) }}</span>
          <button
            @click="removeAttachment"
            aria-label="Quitar archivo adjunto"
            class="ml-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-oroOscuro/70 hover:bg-oro/20 hover:text-oroOscuro"
          >×</button>
        </div>

        <div class="flex min-w-0 items-end gap-1.5 rounded-2xl border border-slate-200 bg-slate-50/70 px-2 py-2 transition-all duration-200 hover:border-slate-300 hover:bg-white focus-within:border-oro/60 focus-within:bg-white focus-within:shadow-[0_8px_24px_rgba(15,23,42,0.08)] sm:gap-2 sm:px-4">
          <input
            ref="fileInput"
            type="file"
            :accept="ATTACHMENT_ACCEPT"
            class="hidden"
            @change="onFileSelected"
          />
          <button
            @click="openFilePicker"
            type="button"
            aria-label="Adjuntar archivo"
            title="Adjuntar archivo (PDF, Word o texto)"
            :disabled="isProcessing"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-slate-200/60 hover:text-azulCorp disabled:opacity-50"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
              <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>

          <textarea
            v-model="promptText"
            rows="1"
            placeholder="Escribe tu consulta..."
            :disabled="isProcessing"
             class="min-h-0 min-w-0 flex-1 resize-none bg-transparent py-1.5 text-sm text-azulCorp outline-none placeholder:text-slate-400 disabled:opacity-50"
            @keydown.enter.exact.prevent="send"
          ></textarea>

          <button
            @click="send"
            aria-label="Enviar consulta"
            :disabled="!canSimulate()"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-[#996515] via-[#D4AF37] to-[#F9D71C] text-white shadow-md hover:shadow-lg hover:shadow-oro/20 hover:scale-105 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
              <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
