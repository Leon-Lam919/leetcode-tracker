// One small function per backend endpoint. All requests go to /api, which the
// Vite dev server (or nginx in Docker) forwards to FastAPI.

// Turns FastAPI's {"detail": ...} into a readable message.
function errorMessage(detail, status) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('; ') // 422 validation errors
  return `Request failed (${status})`
}

async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const error = new Error(errorMessage(body.detail, response.status))
    error.status = response.status
    throw error
  }

  if (response.status === 204) return null // DELETE returns no body
  return response.json()
}

export function getStats() {
  return request('/stats')
}

export function getHeatmap(days = 90) {
  return request(`/heatmap?days=${days}`)
}

// filters: { difficulty, topic, needsReview } — empty values are left out.
export function getSolves(filters = {}) {
  const params = new URLSearchParams()
  if (filters.difficulty) params.set('difficulty', filters.difficulty)
  if (filters.topic) params.set('topic', filters.topic)
  if (filters.needsReview) params.set('needs_review', 'true')
  const query = params.toString()
  return request(query ? `/solves?${query}` : '/solves')
}

export function addSolve(solve) {
  return request('/solves', { method: 'POST', body: JSON.stringify(solve) })
}

export function updateSolve(id, changes) {
  return request(`/solves/${id}`, { method: 'PATCH', body: JSON.stringify(changes) })
}

export function deleteSolve(id) {
  return request(`/solves/${id}`, { method: 'DELETE' })
}

export function syncNow() {
  return request('/sync', { method: 'POST' })
}

export function getDueReviews() {
  return request('/reviews/due')
}

// confidence: 1 = again, 2 = good, 3 = easy
export function markReviewed(problemId, confidence) {
  return request(`/reviews/${problemId}`, {
    method: 'POST',
    body: JSON.stringify({ confidence }),
  })
}
