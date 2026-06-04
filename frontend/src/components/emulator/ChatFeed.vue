<script setup>
import { ref } from 'vue'

const emit = defineEmits(['openDrawer'])

const messages = ref([
  { role: 'system', text: 'Bienvenido al Simulador DAD. Selecciona la entidad y marco normativo, luego escribe tu consulta.' }
])
const input = ref('')

function send() {
  const text = input.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', text })
  input.value = ''
  simulateResponse(text)
}

function simulateResponse(prompt) {
  messages.value.push({ role: 'dad', text: `Analizando solicitud: "${prompt}"\n\n**Resultado preliminar:**\n- Cs: Verificación de costos conforme a NIA 230 — OK\n- Cv: Contexto Venezolano — requiere revisión de Gaceta Oficial\n- CS: Cumplimiento sostenible — pendiente\n- GT: Gestión tributaria — OK\n- NI: Normativa internacional — OK` })
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
        >
          {{ msg.text }}
        </div>

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
    </div>

    <!-- Floating input area -->
    <div class="sticky bottom-0 border-t border-slate-200 bg-white px-4 py-3 shadow-[inset_0_2px_4px_rgba(0,0,0,0.06)]">
      <div class="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white px-4 py-2 shadow-sm">
        <textarea
          v-model="input"
          rows="1"
          placeholder="Escribe tu consulta de auditoría..."
          class="min-h-0 flex-1 resize-none bg-transparent py-1.5 text-sm text-slate-800 outline-none placeholder:text-slate-400"
          @keydown.enter.prevent="send"
        ></textarea>
        <button
          @click="send"
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white transition-colors hover:bg-slate-800 active:bg-slate-700"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
            <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
