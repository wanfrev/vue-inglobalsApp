import { ref } from 'vue'
import { getToken, setToken } from '../services/api.js'

export const currentView = ref('emulator')

export const simulationStatus = ref('idle')
export const promptText = ref('')

export const sessionToken = ref(getToken())
export const sessionInfo = ref(null) // { free_queries_used, free_queries_remaining, is_paid }

export function setView(view) {
  currentView.value = view
}

export function setSession({ token, free_queries_used, free_queries_remaining, is_paid }) {
  sessionToken.value = token
  setToken(token)
  sessionInfo.value = { free_queries_used, free_queries_remaining, is_paid }
}

export function updateSessionStatus({ free_queries_used, free_queries_remaining, is_paid }) {
  if (!sessionInfo.value) return
  sessionInfo.value = { ...sessionInfo.value, free_queries_used, free_queries_remaining, is_paid }
}

export function clearSession() {
  sessionToken.value = ''
  sessionInfo.value = null
  setToken('')
}
