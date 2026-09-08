const BASE_URL = 'http://localhost:8000'

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`
  const headers = options.headers || {}
  
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  
  const res = await fetch(url, {
    ...options,
    headers,
  })
  
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Error ${res.status}`)
  }
  return res.json()
}

export function healthCheck() {
  return request('/')
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
