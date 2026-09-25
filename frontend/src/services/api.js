const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TOKEN_KEY = 'inglobals_token'

// El token vive en memoria como fuente de verdad — localStorage es solo para
// persistir entre recargas. Si localStorage falla en silencio (modo privado,
// restricciones de storage de iOS/Safari, PWA en standalone, etc.), la
// sesión seguía viéndose bien en la UI pero cada request real salía sin
// token porque getToken() dependía 100% de una lectura a localStorage que
// nunca se había guardado. Con el valor en memoria, la sesión sigue
// funcionando durante toda la pestaña aunque no sobreviva un refresh.
let currentToken = (() => {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
})()

export function getToken() {
  return currentToken
}

export function setToken(token) {
  currentToken = token || ''
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // localStorage no disponible — el token sigue sirviendo en memoria para
    // esta pestaña, solo no sobrevive un refresh.
  }
}

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`
  const headers = options.headers || {}

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url, {
    ...options,
    headers,
  })

  if (!res.ok) {
    // Si el servidor ni alcanzó a responder con JSON (típico de un 502/504 de
    // Nginx cuando el backend tardó de más), res.statusText da un
    // "Gateway Time-out" pelado que no le dice nada al usuario.
    const err = await res.json().catch(() => ({}))
    const gatewayMessage = [502, 503, 504].includes(res.status)
      ? 'El servidor tardó demasiado en responder o no está disponible. Intenta de nuevo en un momento.'
      : null
    const error = new Error(err.detail || gatewayMessage || res.statusText || `Error ${res.status}`)
    error.status = res.status
    throw error
  }
  return res.json()
}

export function healthCheck() {
  return request('/')
}

export function startSession() {
  return request('/api/v1/session', { method: 'POST' })
}

export function getSessionStatus() {
  return request('/api/v1/session/me')
}

export function simulate({ prompt }) {
  return request('/api/v1/simulate', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  })
}

export function getHistory({ entityType = null, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams()
  if (entityType) params.append('entity_type', entityType)
  params.append('limit', String(limit))
  params.append('offset', String(offset))
  return request(`/api/v1/history?${params.toString()}`)
}

export function getSimulation(expedienteId) {
  return request(`/api/v1/history/${expedienteId}`)
}

export function exportSimulation(expedienteId) {
  return request(`/api/v1/history/${expedienteId}/export`)
}
