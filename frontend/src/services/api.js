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

export function simulate({ prompt, entity_type, framework }) {
  return request('/api/v1/simulate', {
    method: 'POST',
    body: JSON.stringify({ prompt, entity_type, framework }),
  })
}

export function uploadDocument(file, title, category, date = '') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('title', title)
  formData.append('category', category)
  if (date) formData.append('date', date)
  
  return request('/api/v1/documents/upload', {
    method: 'POST',
    body: formData,
  })
}

export function getDocuments(category = null) {
  const params = category ? `?category=${category}` : ''
  return request(`/api/v1/documents${params}`)
}

export function deleteDocument(docId) {
  return request(`/api/v1/documents/${docId}`, {
    method: 'DELETE',
  })
}

export function searchDocuments(query, topK = 5, filterCategory = null) {
  const formData = new FormData()
  formData.append('query', query)
  formData.append('top_k', String(topK))
  if (filterCategory) formData.append('filter_category', filterCategory)
  
  return request('/api/v1/documents/search', {
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
