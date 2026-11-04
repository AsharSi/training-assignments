import type { LogRow } from './types'

export interface GroupStats {
  key: string
  /** every logged call, including failed ones */
  runs: number
  /** calls that failed (rate limit, bad model name, network…) */
  errors: number
  /** errors / runs */
  errorRate: number
  correct: number
  incorrect: number
  /** successful calls not rated yet */
  unrated: number
  /** correct / rated, null if nothing rated */
  accuracy: number | null
  /** incorrect / rated, null if nothing rated */
  incorrectRate: number | null
  /** (errors + incorrect) / (errors + rated): share of known outcomes that failed */
  failureRate: number | null
  /** share of successful answers that said "could not find that information" */
  notFoundRate: number
  avgSeconds: number | null
  p50Seconds: number | null
  p95Seconds: number | null
  avgDistance: number | null
}

const NOT_FOUND = /could not find that information/i

function percentile(sorted: number[], p: number): number | null {
  if (!sorted.length) return null
  const idx = Math.min(sorted.length - 1, Math.ceil((p / 100) * sorted.length) - 1)
  return sorted[Math.max(0, idx)]
}

const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null)

export const isError = (r: LogRow) => Boolean(r.error)

export function summarize(key: string, rows: LogRow[]): GroupStats {
  // Failed calls count toward runs and error rate only; quality and latency
  // numbers use the successful calls, so a fast failure doesn't look like a fast answer.
  const ok = rows.filter((r) => !isError(r))
  const errors = rows.length - ok.length
  const correct = ok.filter((r) => r.feedback === 'Correct').length
  const incorrect = ok.filter((r) => r.feedback === 'Incorrect').length
  const rated = correct + incorrect
  const secs = ok.map((r) => r.total_seconds).filter((x): x is number => x != null).sort((a, b) => a - b)
  const dists = ok.map((r) => r.best_distance).filter((x): x is number => x != null)
  return {
    key,
    runs: rows.length,
    errors,
    errorRate: rows.length ? errors / rows.length : 0,
    correct,
    incorrect,
    unrated: ok.length - rated,
    accuracy: rated ? correct / rated : null,
    incorrectRate: rated ? incorrect / rated : null,
    failureRate: errors + rated ? (errors + incorrect) / (errors + rated) : null,
    notFoundRate: ok.length ? ok.filter((r) => NOT_FOUND.test(r.answer)).length / ok.length : 0,
    avgSeconds: mean(secs),
    p50Seconds: percentile(secs, 50),
    p95Seconds: percentile(secs, 95),
    avgDistance: mean(dists),
  }
}

export function groupBy(rows: LogRow[], keyOf: (r: LogRow) => string): Map<string, LogRow[]> {
  const map = new Map<string, LogRow[]>()
  for (const r of rows) {
    const k = keyOf(r)
    const list = map.get(k)
    if (list) list.push(r)
    else map.set(k, [r])
  }
  return map
}

/** Questions are compared case/space-insensitively so near-duplicates group together. */
export const normQuestion = (q: string) =>
  q.trim().replace(/\s+/g, ' ').replace(/[\s?.!]+$/, '').toLowerCase()

export const fmtPct = (x: number | null) => (x == null ? '—' : `${Math.round(x * 100)}%`)
export const fmtSec = (x: number | null) => (x == null ? '—' : `${x.toFixed(2)}s`)
export const fmtNum = (x: number | null, d = 3) => (x == null ? '—' : x.toFixed(d))
