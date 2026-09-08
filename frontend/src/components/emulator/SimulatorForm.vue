<script setup>
import { ref } from 'vue'
import { simulate } from '../../services/api.js'
import { promptText, simulationStatus } from '../../stores/appStore.js'

const messages = ref([])
const isProcessing = ref(false)
const fileInput = ref(null)
const attachedFiles = ref([])

function canSimulate() {
  return promptText.value.trim().length > 0 && !isProcessing.value
}

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  const picked = Array.from(event.target.files || [])
  attachedFiles.value.push(...picked)
  event.target.value = ''
}

function removeFile(index) {
  attachedFiles.value.splice(index, 1)
}

async function send() {
  if (!canSimulate()) return

  const text = promptText.value
  const files = [...attachedFiles.value]

  isProcessing.value = true
  simulationStatus.value = 'processing'

  messages.value.push({
    role: 'user',
    text,
    fileNames: files.map((f) => f.name),
  })
  promptText.value = ''
  attachedFiles.value = []

  try {
    const result = await simulate({ prompt: text, files })

    if (result.structured_prompt && result.structured_prompt !== text) {
      messages.value.push({
        role: 'structured',
        text: result.structured_prompt,
        entityType: result.entity_type,
        framework: result.framework,
      })
    }

    if (result.question_well_formed === false) {
      messages.value.push({
        role: 'alert',
        text: result.question_feedback || 'La pregunta necesita más información para evaluarse con rigor.',
        failedVar: 'Pregunta incompleta',
      })
    }

    messages.value.push({
      role: 'dad',
      text: formatResponse(result),
    })

    messages.value.push({
      role: 'usage',
      usage: result.usage,
    })

    if (!result.is_valid) {
      const failedCriteria = Object.entries(result.criteria)
        .filter(([_, v]) => v.status === 'failed')
        .map(([k]) => k)

      if (failedCriteria.length > 0) {
        messages.value.push({
          role: 'alert',
          text:
            result.corrective_action ||
            'Se detectaron incumplimientos. Revisa los criterios marcados.',
          failedVar: failedCriteria.join(', '),
        })
      }
    }
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

function formatResponse(result) {
  const statusIcon = (s) => (s === 'passed' ? '✓' : '✗')
  const statusText = (s) => (s === 'passed' ? 'OK' : 'FALLÓ')

  let text = `**${result.summary}**\n\n`
  text += `**Expediente:** ${result.expediente_id}\n`
  text += `**Score de Cumplimiento:** ${result.compliance_score}%\n\n`
  text += `**Criterios DAD:**\n`

  for (const [key, criterion] of Object.entries(result.criteria)) {
    text += `- ${key}: ${statusIcon(criterion.status)} ${statusText(criterion.status)}\n`
    text += `  ${criterion.detail}\n`
    if (criterion.article_ref) {
      text += `  _Ref: ${criterion.article_ref}_\n`
    }
  }

  if (result.corrective_action) {
    text += `\n**Acción Correctiva:** ${result.corrective_action}`
  }

  return text
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
            <div v-if="msg.fileNames?.length" class="mt-2 flex flex-wrap gap-1">
              <span
                v-for="name in msg.fileNames"
                :key="name"
                class="rounded-md bg-oro/15 px-2 py-0.5 text-[10px] font-bold text-oroOscuro"
              >📎 {{ name }}</span>
            </div>
          </div>
        </div>

        <!-- Pregunta reformulada por el Prompt 1 (organizador) -->
        <div v-else-if="msg.role === 'structured'" class="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-sm">
          <span class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white text-xs font-bold text-slate-500">02</span>
          <div class="min-w-0 flex-1 break-words">
            <p class="mb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Pregunta organizada</p>
            <p class="text-sm text-slate-700 leading-relaxed">{{ msg.text }}</p>
            <p v-if="msg.entityType || msg.framework" class="mt-2 text-[11px] text-slate-400">
              Entidad detectada: {{ msg.entityType }} · Marco: {{ msg.framework }}
            </p>
          </div>
        </div>

        <!-- Respuesta DAD -->
        <div
          v-else-if="msg.role === 'dad'"
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.05)]"
        >
          <div
            class="break-words text-sm leading-relaxed text-slate-800 whitespace-pre-line"
            v-html="
              msg.text
                .replace(/\*\*(.*?)\*\*/g, '<strong class=\'text-azulCorp\'>$1</strong>')
                .replace(/_(.*?)_/g, '<em class=\'text-slate-500\'>$1</em>')
            "
          ></div>
        </div>

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

        <!-- Consumo de tokens / costo (Prompt 2) -->
        <div
          v-else-if="msg.role === 'usage' && msg.usage"
          class="flex flex-wrap items-center gap-x-4 gap-y-1 px-1 text-[11px] text-slate-400"
        >
          <span class="break-words">{{ msg.usage.total_tokens }} tokens ({{ msg.usage.prompt_tokens }} entrada / {{ msg.usage.completion_tokens }} salida)</span>
          <span>≈ ${{ msg.usage.estimated_cost_usd.toFixed(6) }} USD</span>
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
        <div v-if="attachedFiles.length" class="mb-2 flex flex-wrap gap-1.5">
          <span
            v-for="(file, i) in attachedFiles"
            :key="i"
            class="inline-flex max-w-full items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
          >
                <span class="truncate">{{ file.name }}</span>
            <button @click="removeFile(i)" class="text-slate-400 hover:text-slate-700">✕</button>
          </span>
        </div>

        <div class="flex min-w-0 items-end gap-1.5 rounded-2xl border border-slate-200 bg-slate-50/70 px-2 py-2 transition-all duration-200 hover:border-slate-300 hover:bg-white focus-within:border-oro/60 focus-within:bg-white focus-within:shadow-[0_8px_24px_rgba(15,23,42,0.08)] sm:gap-2 sm:px-4">
          <button
            @click="openFilePicker"
            title="Adjuntar archivo (PDF, Word, Excel o TXT)"
             class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-slate-100 hover:text-oroOscuro"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
              <path d="M21.44 11.05l-9.19 9.19a5 5 0 0 1-7.07-7.07l9.19-9.19a3 3 0 0 1 4.24 4.24l-9.2 9.19a1 1 0 0 1-1.41-1.41l8.49-8.48" />
            </svg>
          </button>
          <input ref="fileInput" type="file" accept=".pdf,.txt,.docx,.xlsx" multiple class="hidden" @change="handleFileChange" />

          <textarea
            v-model="promptText"
            rows="1"
            placeholder="Escribe tu consulta de auditoría..."
            :disabled="isProcessing"
             class="min-h-0 min-w-0 flex-1 resize-none bg-transparent py-1.5 text-sm text-azulCorp outline-none placeholder:text-slate-400 disabled:opacity-50"
            @keydown.enter.exact.prevent="send"
          ></textarea>

          <button
            @click="send"
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
