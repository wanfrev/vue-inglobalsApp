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

async function throwFromResponse(res) {
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

async function authorizedFetch(endpoint, options = {}) {
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
  if (!res.ok) await throwFromResponse(res)
  return res
}

async function request(endpoint, options = {}) {
  const res = await authorizedFetch(endpoint, options)
  return res.json()
}

export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
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

// El endpoint pasó de JSON a multipart/form-data para poder mandar el
// archivo adjunto opcional (ver ATTACHMENT_MAX_FILE_SIZE_MB en el backend);
// se manda como FormData siempre, con o sin archivo, para tener un solo
// camino — request() ya detecta FormData y no le pisa el Content-Type
// (el navegador pone el boundary del multipart automáticamente).
export function simulate({ prompt, file }) {
  const formData = new FormData()
  formData.append('prompt', prompt)
  if (file) formData.append('file', file)
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

// Descarga de la respuesta (o del modelo generado) en PDF — a pedido del
// cliente nunca se descarga en JSON. El servidor arma el PDF con la consulta,
// la respuesta y la bibliografía consultada (sin la trazabilidad interna).
export async function downloadAnswerPdf(expedienteId) {
  const res = await authorizedFetch(`/api/v1/history/${expedienteId}/export`)
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^";]+)"?/)
  saveBlob(await res.blob(), match ? match[1] : `respuesta-${expedienteId}.pdf`)
}

// URL pública de descarga de una ley de la bibliografía (solo las que tienen
// original disponible; ver `downloadable` en las fuentes de cada respuesta).
export function documentDownloadUrl(docId) {
  return `${BASE_URL}/api/v1/documents/${docId}/download`
}

// Flujo en dos pasos: 1) reformulación + Loop 1 -> el usuario decide cómo
// seguir; 2) respuesta final / búsqueda externa / generar un modelo.
export function simulateStart({ prompt, file }) {
  const formData = new FormData()
  formData.append('prompt', prompt)
  if (file) formData.append('file', file)
  return request('/api/v1/simulate/start', { method: 'POST', body: formData })
}

export function simulateFinalize({ draftId, mode, kind = '', file = null }) {
  const formData = new FormData()
  formData.append('draft_id', draftId)
  formData.append('mode', mode)
  if (kind) formData.append('kind', kind)
  if (file) formData.append('file', file)
  return request('/api/v1/simulate/finalize', { method: 'POST', body: formData })
}
