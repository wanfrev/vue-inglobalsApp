<script setup>
import { ref } from 'vue'
import { login, register } from '../services/api.js'
import { loginSession } from '../stores/appStore.js'

const mode = ref('register') // 'register' | 'login'
const email = ref('')
const password = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

function toggleMode() {
  mode.value = mode.value === 'register' ? 'login' : 'register'
  errorMessage.value = ''
}

async function submit() {
  if (isSubmitting.value) return
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const action = mode.value === 'register' ? register : login
    const auth = await action(email.value.trim(), password.value)
    loginSession(auth)
  } catch (error) {
    errorMessage.value = error.message || 'No se pudo completar la solicitud'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-1 items-center justify-center px-4 py-10">
    <div class="soft-panel w-full max-w-sm space-y-5 rounded-[28px] p-6 sm:p-8">
      <div class="text-center">
        <h1 class="text-lg font-bold text-azulCorp">
          {{ mode === 'register' ? 'Crear cuenta' : 'Iniciar sesión' }}
        </h1>
        <p class="mt-1 text-sm text-slate-500">
          {{ mode === 'register' ? 'Registro rápido — 3 consultas gratis para probar.' : 'Ingresa con tu correo y contraseña.' }}
        </p>
      </div>

      <form class="space-y-3" @submit.prevent="submit">
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-500">Correo</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="tu@correo.com"
            class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-azulCorp outline-none focus:border-oro"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-500">Contraseña</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="8"
            placeholder="Mínimo 8 caracteres"
            class="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-azulCorp outline-none focus:border-oro"
          />
        </div>

        <p v-if="errorMessage" class="text-sm font-medium text-red-600">{{ errorMessage }}</p>

        <button
          type="submit"
          :disabled="isSubmitting"
          class="w-full rounded-xl bg-gradient-to-r from-[#996515] to-[#D4AF37] px-4 py-2.5 text-sm font-bold text-white shadow-md transition-all hover:shadow-lg hover:shadow-oro/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {{ isSubmitting ? 'Un momento...' : (mode === 'register' ? 'Crear cuenta' : 'Entrar') }}
        </button>
      </form>

      <button
        @click="toggleMode"
        class="w-full text-center text-xs font-medium text-slate-500 hover:text-oroOscuro"
      >
        {{ mode === 'register' ? '¿Ya tienes cuenta? Inicia sesión' : '¿No tienes cuenta? Regístrate' }}
      </button>
    </div>
  </div>
</template>
