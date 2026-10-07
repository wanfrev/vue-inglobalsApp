import { ref } from 'vue'
import { getToken, setToken } from '../services/api.js'

export const currentView = ref('emulator')

export const simulationStatus = ref('idle')
export const promptText = ref('')

export const sessionToken = ref(getToken())
// Sin límite de consultas (a pedido del cliente) — ya no se guarda
// "free_queries_remaining", solo el contador informativo y el estado pagado.
export const sessionInfo = ref(null) // { free_queries_used, is_paid }

export function setView(view) {
  currentView.value = view
}

export function setSession({ token, free_queries_used, is_paid }) {
  sessionToken.value = token
  setToken(token)
  sessionInfo.value = { free_queries_used, is_paid }
}

export function updateSessionStatus({ free_queries_used, is_paid }) {
  if (!sessionInfo.value) return
  sessionInfo.value = { ...sessionInfo.value, free_queries_used, is_paid }
}

// --- Cuestionario del cliente --------------------------------------------
// "Completado" se guarda en el navegador (igual que la sesión anónima): si la
// persona borra los datos del sitio, el botón vuelve a habilitarse.
const SURVEY_KEY = 'inglobals_survey_completed'

function readSurveyFlag() {
  try {
    return localStorage.getItem(SURVEY_KEY) === '1'
  } catch {
    return false
  }
}

export const surveyCompleted = ref(readSurveyFlag())
// Se abrió el formulario y falta confirmar que se envió (ver SurveyButton.vue).
export const surveyAwaitingConfirmation = ref(false)

export function noteSurveyOpened() {
  surveyAwaitingConfirmation.value = true
}

export function dismissSurveyConfirmation() {
  surveyAwaitingConfirmation.value = false
}

export function markSurveyCompleted() {
  surveyCompleted.value = true
  surveyAwaitingConfirmation.value = false
  try {
    localStorage.setItem(SURVEY_KEY, '1')
  } catch {
    // Sin localStorage el estado vale solo para esta pestaña.
  }
}

// Registro automático: el mensaje de confirmación del formulario de Google puede
// llevar un enlace de vuelta a /simulador/?cuestionario=completado.
try {
  const params = new URLSearchParams(window.location.search)
  if (params.get('cuestionario') === 'completado') {
    markSurveyCompleted()
    params.delete('cuestionario')
    const query = params.toString()
    window.history.replaceState({}, '', `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`)
  }
} catch {
  // Entorno sin window/history (no debería pasar en el navegador).
}

export function clearSession() {
  sessionToken.value = ''
  sessionInfo.value = null
  setToken('')
}
