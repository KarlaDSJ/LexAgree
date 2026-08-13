const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Pipeline steps in order. The backend can send any of these
// keys in "status"; STEP_ORDER determines which step number (1-5) to display.
export const STEP_ORDER = ['queued', 'segmenting', 'extracting', 'aligning', 'agreement', 'done']

export const STEP_LABELS = {
  segmenting: 'Segmenting the document',
  extracting: 'Extracting arguments (multi-LLM)',
  aligning: 'Aligning with the original text',
  agreement: 'Computing agreement between models',
  done: 'Done',
}

export const AVAILABLE_MODELS = [
  { id: 'llama', label: 'Llama 3.1 8B Instruct' },
  { id: 'qwen', label: 'Qwen 2.5 7B Instruct' },
  { id: 'saul', label: 'Saul 7B Instruct' },
]

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function handleResponse(res) {
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body.error || body.message || body.detail || ''
    } catch {
      // respuesta sin cuerpo JSON
    }
    throw new ApiError(detail || `Server error (${res.status})`, res.status)
  }
  return res.json()
}

export async function uploadDocument(file, selectedModels) {
  const formData = new FormData()
  formData.append('file', file)
  for (const modelId of selectedModels) {
    formData.append('models', modelId)
  }
  const res = await fetch(`${API_BASE}/api/documents`, {
    method: 'POST',
    body: formData,
  })
  return handleResponse(res)
}

export async function getStatus(jobId) {
  const res = await fetch(`${API_BASE}/api/documents/${jobId}/status`)
  return handleResponse(res)
}

export async function getResults(jobId) {
  const res = await fetch(`${API_BASE}/api/documents/${jobId}/results`)
  return handleResponse(res)
}

export { ApiError, API_BASE }