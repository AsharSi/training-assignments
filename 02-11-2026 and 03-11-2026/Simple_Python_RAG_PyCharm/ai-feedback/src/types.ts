export type Feedback = 'Correct' | 'Incorrect' | 'Not rated'

/** One row of rag_feedback.csv, as returned by the backend. */
export interface LogRow {
  index: number
  timestamp: string
  model: string
  question: string
  answer: string
  retrieved_chunk_ids: string
  best_distance: number | null
  total_seconds: number | null
  feedback: Feedback
  /** Why the call failed; empty string when it succeeded. */
  error: string
}

export interface ChunkMatch {
  id: string
  source: string
  distance: number
  text: string
}

export interface AskResult extends LogRow {
  retrieval_seconds: number
  matches: ChunkMatch[]
}

export interface Health {
  ok: boolean
  default_model: string
  has_api_key: boolean
  log_path: string
}

/** Saved in localStorage. */
export interface SavedModel {
  id: string
  name: string // OpenRouter model slug, e.g. "openai/gpt-4o-mini"
  note: string
}

export interface SavedQuestion {
  id: string
  text: string
  category: string
}

/** One model × question call in an Ask & Rate run. */
export interface RunJob {
  key: string
  model: string
  question: string
  status: 'queued' | 'running' | 'done' | 'error'
  result?: AskResult
  error?: string
}
