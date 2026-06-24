<script setup>
import { ref } from 'vue'
import { simulate } from '../../services/api.js'
import {
  promptText,
  entityType,
  framework,
  simulationStatus,
  dadVariables,
  resetDadVariables,
  updateDadVariablesFromResult,
  addToHistory,
  canSimulate,
  getActiveVariableCount,
} from '../../stores/appStore.js'
import DADPanel from './DADPanel.vue'

const messages = ref([])
const isProcessing = ref(false)
const promptLocked = ref(false)

function lockPrompt() {
  if (promptText.value.trim().length > 0) {
    promptLocked.value = true
  }
}

function unlockPrompt() {
  promptLocked.value = false
}

async function send() {
  if (!canSimulate() || isProcessing.value) return

  const activeVars = Object.entries(dadVariables)
    .filter(([_, v]) => v.active)
    .map(([k]) => k)

  isProcessing.value = true
  simulationStatus.value = 'processing'
  resetDadVariables()

  messages.value.push({
    role: 'user',
    text: promptText.value,
    vars: activeVars,
  })

  try {
    const result = await simulate({
      prompt: promptText.value,
      entity_type: entityType.value,
      framework: framework.value,
    })

    updateDadVariablesFromResult(result)

    messages.value.push({
      role: 'dad',
      text: formatResponse(result),
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

    addToHistory({
      expediente_id: result.expediente_id,
      created_at: result.created_at,
      entity_type: entityType.value,
      framework: framework.value,
      prompt: promptText.value,
      is_valid: result.is_valid,
      compliance_score: result.compliance_score,
    })
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
  <div class="flex flex-1 flex-col overflow-y-auto">
    <!-- Prompt Area -->
    <div class="border-b border-slate-200 bg-white/80 backdrop-blur-sm px-4 py-5 lg:px-8">
      <label class="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
        Instrucción de Simulación (Prompt)
      </label>
      <div class="relative">
        <textarea
          v-model="promptText"
          rows="3"
          placeholder="Escribe aquí los criterios, objetivos o el enfoque específico que la IA utilizará para evaluar los documentos almacenados..."
          :disabled="promptLocked"
          class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-sm text-azulCorp outline-none transition-all placeholder:text-slate-400 focus:border-oro disabled:bg-slate-100 disabled:text-slate-500 resize-none"
        ></textarea>
        <button
          v-if="!promptLocked"
          @click="lockPrompt"
          :disabled="!promptText.trim()"
          class="absolute bottom-3 right-3 rounded-xl border border-oro/30 px-3 py-1.5 text-xs font-semibold text-oroOscuro transition-all hover:bg-oro/10 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Fijar Parámetros
        </button>
        <button
          v-else
          @click="unlockPrompt"
          class="absolute bottom-3 right-3 rounded-xl border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-500 transition-all hover:bg-slate-100"
        >
          Editar
        </button>
      </div>
    </div>

    <!-- DAD Variables Section -->
    <div class="border-b border-slate-200 bg-white/50 px-4 py-5 lg:px-8">
      <div class="mb-3 flex items-center justify-between">
        <label class="text-xs font-bold uppercase tracking-wider text-slate-500">
          Ecuación DAD (Selecciona las variables a procesar)
        </label>
        <span class="text-[11px] font-medium text-slate-400">
          {{ getActiveVariableCount() }} de 5 activas
        </span>
      </div>
      <DADPanel />
    </div>

    <!-- Simulate Button Area -->
    <div class="border-b border-slate-200 bg-white px-4 py-5 lg:px-8">
      <button
        @click="send"
        :disabled="!canSimulate() || isProcessing"
        class="w-full rounded-2xl px-6 py-4 text-sm font-bold transition-all duration-300"
        :class="
          canSimulate() && !isProcessing
            ? 'bg-gradient-to-r from-[#996515] to-[#D4AF37] text-white shadow-lg hover:shadow-xl hover:shadow-oro/20 hover:-translate-y-0.5 active:scale-[0.99]'
            : 'bg-slate-200 text-slate-400 cursor-not-allowed'
        "
      >
        <template v-if="isProcessing">
          <span class="flex items-center justify-center gap-2">
            <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Procesando con IA...
          </span>
        </template>
        <template v-else>
          Simular
        </template>
      </button>
      <p class="mt-2 text-center text-[11px] text-slate-400">
        {{ canSimulate() ? 'Presiona para procesar las variables activas con las instrucciones del prompt' : 'Escribe un prompt y activa al menos una variable para comenzar' }}
      </p>
    </div>

    <!-- Results / Messages Feed -->
    <div class="flex-1 space-y-4 bg-white/50 px-4 py-5 lg:px-8">
      <div
        v-if="!messages.length"
        class="flex flex-col items-center justify-center py-16 text-center"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="mb-4 h-12 w-12 text-slate-300"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <path d="M7 10l5-5 5 5" />
          <path d="M12 5v12" />
        </svg>
        <p class="text-sm text-slate-400">Los resultados de la simulación aparecerán aquí</p>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="mx-auto w-full max-w-3xl space-y-1"
      >
        <!-- Prompt enviado -->
        <div v-if="msg.role === 'user'" class="flex items-start gap-3 rounded-2xl border border-oro/20 bg-oro/5 p-4">
          <span class="mt-0.5 shrink-0 text-sm">📝</span>
          <div class="min-w-0 flex-1">
            <p class="mb-1 text-[11px] font-semibold uppercase tracking-wider text-oroOscuro">Prompt Enviado</p>
            <p class="text-sm text-azulCorp leading-relaxed">{{ msg.text }}</p>
            <div v-if="msg.vars?.length" class="mt-2 flex flex-wrap gap-1">
              <span
                v-for="v in msg.vars"
                :key="v"
                class="rounded-md bg-oro/15 px-2 py-0.5 text-[10px] font-bold text-oroOscuro"
              >{{ v }}</span>
            </div>
          </div>
        </div>

        <!-- Respuesta DAD -->
        <div
          v-else-if="msg.role === 'dad'"
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div
            class="text-sm text-slate-800 leading-relaxed whitespace-pre-line"
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
          class="rounded-2xl border-l-4 border-l-violetaIA bg-violetaIA/5 p-4"
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
          <p class="text-sm text-slate-700 whitespace-pre-line">{{ msg.text }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
