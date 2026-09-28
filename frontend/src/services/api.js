const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path) {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) throw new Error('Could not load your incident data. Check that the backend is running.')
  return response.json()
}

export async function sendMessage(message, conversationId) {
  let response
  try {
    response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    })
  } catch {
    throw new Error('Could not reach Rootmind-AI. Check that the backend is running.')
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || 'The assistant could not complete this request. Please try again.')
  }
  return response.json()
}

export const getProblems = () => request('/api/problems')
export const getMemory = () => request('/api/memory')
