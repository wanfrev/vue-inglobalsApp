const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TOKEN_KEY = 'inglobals_token'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // localStorage no disponible (modo privado, etc.) — la sesión no persiste entre recargas
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
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const error = new Error(err.detail || `Error ${res.status}`)
    error.status = res.status
    throw error
  }
  return res.json()
}

export function healthCheck() {
  return request('/')
}

export function register(email, password) {
  return request('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function login(email, password) {
  return request('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getMe() {
  return request('/api/v1/auth/me')
}

export function simulate({ prompt, files = [] }) {
  const formData = new FormData()
  formData.append('prompt', prompt)
  for (const file of files) {
    formData.append('files', file)
  }

  return request('/api/v1/simulate', {
    method: 'POST',
    body: formData,
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
