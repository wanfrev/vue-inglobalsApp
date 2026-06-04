<script setup>
import { ref } from 'vue'

const messages = ref([])
const input = ref('')

function send() {
  const text = input.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', text })
  input.value = ''
  setTimeout(() => {
    messages.value.push({ role: 'dad', text: `Simulando auditoría para: "${text}"` })
  }, 500)
}
</script>

<template>
  <div class="flex flex-1 flex-col">
    <div class="flex-1 space-y-3 overflow-y-auto px-4 py-4">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="max-w-[85%] rounded-lg px-4 py-2 text-sm leading-relaxed"
        :class="msg.role === 'user'
          ? 'ml-auto bg-navy-700 text-slate-100'
          : 'bg-slate-800 text-slate-300'"
      >
        {{ msg.text }}
      </div>
      <p v-if="!messages.length" class="mt-10 text-center text-sm text-slate-600">
        Selecciona entidad y marco normativo, luego presiona Simular.
      </p>
    </div>
    <div class="border-t border-slate-800 px-4 py-3">
      <div class="flex gap-2">
        <input
          v-model="input"
          type="text"
          placeholder="Escribe tu consulta..."
          class="min-w-0 flex-1 rounded border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none placeholder:text-slate-500 focus:border-navy-500"
          @keydown.enter="send"
        />
        <button
          @click="send"
          class="rounded bg-navy-600 px-4 text-white transition-colors hover:bg-navy-500"
        >
          ➤
        </button>
      </div>
    </div>
  </div>
</template>
