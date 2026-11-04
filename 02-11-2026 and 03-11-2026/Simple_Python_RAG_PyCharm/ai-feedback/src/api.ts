import type { AskResult, Feedback, Health, LogRow } from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new Error('Backend not reachable. Is feedback_api.py running on port 8000?')
  }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<Health>('/api/health'),
  logs: () => request<LogRow[]>('/api/logs'),
  ask: (question: string, model: string, topK: number, signal?: AbortSignal) =>
    request<AskResult>('/api/ask', {
      method: 'POST',
      body: JSON.stringify({ question, model, top_k: topK }),
      signal,
    }),
  setFeedback: (index: number, feedback: Feedback) =>
    request<LogRow>(`/api/logs/${index}`, {
      method: 'PATCH',
      body: JSON.stringify({ feedback }),
    }),
}
