import { ref } from 'vue'
import { getToken, setToken } from '../services/api.js'

export const currentView = ref('emulator')

export const simulationStatus = ref('idle')
export const promptText = ref('')

export const authToken = ref(getToken())
export const currentUser = ref(null) // { email, free_queries_used, free_queries_remaining, is_paid }

export function setView(view) {
  currentView.value = view
}

export function loginSession({ token, email, free_queries_used, free_queries_remaining, is_paid }) {
  authToken.value = token
  setToken(token)
  currentUser.value = { email, free_queries_used, free_queries_remaining, is_paid }
}

export function updateUserStatus({ free_queries_used, free_queries_remaining, is_paid }) {
  if (!currentUser.value) return
  currentUser.value = {
    ...currentUser.value,
    free_queries_used,
    free_queries_remaining,
    is_paid,
  }
}

export function logoutSession() {
  authToken.value = ''
  currentUser.value = null
  setToken('')
  currentView.value = 'emulator'
}
