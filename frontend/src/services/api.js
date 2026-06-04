const BASE_URL = 'http://localhost:8000'

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
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

export function simulate(prompt) {
  return request('/api/simulate', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  })
}
