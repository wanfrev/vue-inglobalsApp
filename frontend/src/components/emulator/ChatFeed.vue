<script setup>
import { ref, watch } from 'vue'
import { simulate } from '../../services/api.js'
import { 
  entityType, 
  framework, 
  simulationStatus,
  resetDadVariables,
  updateDadVariablesFromResult,
  addToHistory
} from '../../stores/appStore.js'

const emit = defineEmits(['openDrawer'])

const messages = ref([
  { role: 'system', text: 'Bienvenido al Simulador DAD. Selecciona la entidad y marco normativo, luego escribe tu consulta.' }
])
const input = ref('')
const isProcessing = ref(false)

async function send() {
  const text = input.value.trim()
  if (!text || isProcessing.value) return
  
  messages.value.push({ role: 'user', text })
  input.value = ''
  isProcessing.value = true
  simulationStatus.value = 'processing'
  resetDadVariables()
  
  try {
    const result = await simulate({
      prompt: text,
      entity_type: entityType.value,
      framework: framework.value
    })
    
    updateDadVariablesFromResult(result)
    
    const responseText = formatResponse(result)
    messages.value.push({ role: 'dad', text: responseText })
    
    if (!result.is_valid) {
      const failedCriteria = Object.entries(result.criteria)
        .filter(([_, v]) => v.status === 'failed')
        .map(([k]) => k)
      
      if (failedCriteria.length > 0) {
        messages.value.push({
          role: 'alert',
          text: result.corrective_action || 'Se detectaron incumplimientos. Revisa los criterios marcados.',
          failedVar: failedCriteria.join(', ')
        })
      }
    }
    
    addToHistory({
      expediente_id: result.expediente_id,
      created_at: result.created_at,
      entity_type: entityType.value,
      framework: framework.value,
      prompt: text,
      is_valid: result.is_valid,
      compliance_score: result.compliance_score
    })
    
  } catch (error) {
    messages.value.push({
      role: 'alert',
      text: `Error al procesar la solicitud: ${error.message}`
    })
  } finally {
    isProcessing.value = false
    simulationStatus.value = 'idle'
  }
}

function formatResponse(result) {
  const statusIcon = (s) => s === 'passed' ? '✓' : '✗'
  const statusText = (s) => s === 'passed' ? 'OK' : 'FALLÓ'
  
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

function reboundExample() {
  messages.value.push({
    role: 'user',
    text: 'Verificar balance general 2024 con legislación venezolana'
  })
  setTimeout(() => {
    messages.value.push({
      role: 'alert',
      text: `**Fallo en Cv — Contexto Venezolano**\n\nEl artículo 7 de la Providencia SENIAT N° 2024-001 no está siendo contemplado en la\nestimación del ajuste por inflación fiscal.\n\n**Recomendación:** Revisar la Gaceta Oficial N° 42.890 y actualizar el marco normativo\nen el repositorio antes de continuar.`,
      failedVar: 'Cv'
    })
  }, 600)
}

watch(simulationStatus, (newStatus) => {
  if (newStatus === 'processing') {
    isProcessing.value = true
  }
})
</script>

<template>
  <div class="flex flex-1 flex-col bg-white">
    <!-- Mobile top bar with drawer toggle -->
    <div class="flex items-center justify-between border-b border-slate-200 px-4 py-2 lg:hidden">
      <button
        @click="emit('openDrawer')"
        class="flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 active:bg-slate-200"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        Configurar
      </button>
      <button
        @click="reboundExample"
        class="text-xs text-rose-600 hover:text-rose-700"
        title="Mostrar ejemplo de rebote"
      >
        Probar alerta
      </button>
    </div>

    <!-- Messages feed -->
    <div class="flex-1 space-y-4 overflow-y-auto px-4 py-5">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="max-w-[88%] text-sm leading-relaxed"
        :class="{
          'ml-auto': msg.role === 'user',
          'mr-auto': msg.role === 'dad' || msg.role === 'alert' || msg.role === 'system',
        }"
      >
        <!-- User bubble -->
        <div
          v-if="msg.role === 'user'"
          class="bg-slate-900 text-white rounded-2xl rounded-tr-none px-4 py-2.5"
        >
          {{ msg.text }}
        </div>

        <!-- System message -->
        <div
          v-else-if="msg.role === 'system'"
          class="text-center text-xs text-slate-400"
        >
          {{ msg.text }}
        </div>

        <!-- AI normal response -->
        <div
          v-else-if="msg.role === 'dad'"
          class="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-none px-4 py-2.5 whitespace-pre-line"
          v-html="msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/_(.*?)_/g, '<em>$1</em>')"
        ></div>

        <!-- Rebound alert -->
        <div
          v-else-if="msg.role === 'alert'"
          class="bg-rose-50 border-l-4 border-l-rose-500 text-rose-950 rounded-r-xl px-4 py-3 whitespace-pre-line"
        >
          <div class="mb-1 flex items-center gap-2">
            <span class="text-sm font-bold">⚠ Alerta de Rebote</span>
            <span
              v-if="msg.failedVar"
              class="rounded bg-rose-200 px-1.5 py-0.5 text-[11px] font-semibold uppercase text-rose-800"
            >
              {{ msg.failedVar }}
            </span>
          </div>
          {{ msg.text }}
        </div>
      </div>
      
      <!-- Processing indicator -->
      <div
        v-if="isProcessing"
        class="mr-auto max-w-[88%]"
      >
        <div class="inline-flex items-center gap-2 rounded-2xl rounded-tl-none border border-slate-200 bg-white px-4 py-2.5">
          <div class="flex gap-1">
            <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]"></span>
            <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]"></span>
            <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400"></span>
          </div>
          <span class="text-xs text-slate-500">Analizando con motor DAD...</span>
        </div>
      </div>
    </div>

    <!-- Floating input area -->
    <div class="sticky bottom-0 border-t border-slate-200 bg-white px-4 py-3 shadow-[inset_0_2px_4px_rgba(0,0,0,0.06)]">
      <div class="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white px-4 py-2 shadow-sm">
        <textarea
          v-model="input"
          rows="1"
          placeholder="Escribe tu consulta de auditoría..."
          :disabled="isProcessing"
          class="min-h-0 flex-1 resize-none bg-transparent py-1.5 text-sm text-slate-800 outline-none placeholder:text-slate-400 disabled:opacity-50"
          @keydown.enter.prevent="send"
        ></textarea>
        <button
          @click="send"
          :disabled="isProcessing"
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white transition-colors hover:bg-slate-800 active:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
            <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
