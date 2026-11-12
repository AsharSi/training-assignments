import { Fragment, useMemo, useState } from 'react'
import { api } from '../api'
import type { Feedback, LogRow } from '../types'
import { FeedbackButtons, FeedbackBadge } from './FeedbackButtons'
import { downloadCsv, fileStamp, type CsvColumn } from '../csv'

// Same columns as rag_feedback.csv, plus the row index.
const LOG_COLUMNS: CsvColumn<LogRow>[] = [
  { header: 'log_index', value: (r) => r.index },
  { header: 'timestamp', value: (r) => r.timestamp },
  { header: 'model', value: (r) => r.model },
  { header: 'question', value: (r) => r.question },
  { header: 'answer', value: (r) => r.answer },
  { header: 'retrieved_chunk_ids', value: (r) => r.retrieved_chunk_ids },
  { header: 'best_distance', value: (r) => r.best_distance },
  { header: 'total_seconds', value: (r) => r.total_seconds },
  { header: 'feedback', value: (r) => r.feedback },
]

interface Props {
  logs: LogRow[]
  setLogs: (fn: (rows: LogRow[]) => LogRow[]) => void
  onRefresh: () => void
  loading: boolean
}

export function LogsPanel({ logs, setLogs, onRefresh, loading }: Props) {
  const [model, setModel] = useState('')
  const [feedback, setFeedback] = useState('')
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState<number | null>(null)
  const [error, setError] = useState('')

  const models = useMemo(() => [...new Set(logs.map((r) => r.model))].sort(), [logs])
  const rows = useMemo(() => {
    const s = search.trim().toLowerCase()
    return logs
      .filter((r) => (!model || r.model === model) && (!feedback || r.feedback === feedback))
      .filter((r) => !s || r.question.toLowerCase().includes(s) || r.answer.toLowerCase().includes(s))
      .slice()
      .reverse() // newest first
  }, [logs, model, feedback, search])

  const rate = async (row: LogRow, f: Feedback) => {
    setLogs((all) => all.map((r) => (r.index === row.index ? { ...r, feedback: f } : r)))
    try {
      await api.setFeedback(row.index, f)
      setError('')
    } catch (e) {
      setLogs((all) => all.map((r) => (r.index === row.index ? { ...r, feedback: row.feedback } : r)))
      setError((e as Error).message)
    }
  }

  return (
    <div className="stack">
      <div className="card toolbar">
        <select value={model} onChange={(e) => setModel(e.target.value)} aria-label="Filter by model">
          <option value="">All models</option>
          {models.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <select value={feedback} onChange={(e) => setFeedback(e.target.value)} aria-label="Filter by feedback">
          <option value="">All feedback</option>
          <option>Correct</option>
          <option>Incorrect</option>
          <option>Not rated</option>
        </select>
        <input className="grow" placeholder="Search question or answer…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <span className="muted">{rows.length} of {logs.length}</span>
        <button onClick={onRefresh} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</button>
        <button disabled={!rows.length} onClick={() => downloadCsv(`rag-feedback-log_${fileStamp()}.csv`, rows, LOG_COLUMNS)}>
          Export CSV
        </button>
      </div>
      {error && <div className="notice error">{error}</div>}

      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Time</th>
              <th>Model</th>
              <th>Question</th>
              <th className="num">Seconds</th>
              <th className="num">Best dist.</th>
              <th>Chunks</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <Fragment key={r.index}>
                <tr className="clickable" onClick={() => setOpen(open === r.index ? null : r.index)} aria-expanded={open === r.index}>
                  <td className="muted">{r.index}</td>
                  <td className="nowrap">{r.timestamp.replace('T', ' ')}</td>
                  <td><code>{r.model}</code></td>
                  <td>{r.question}</td>
                  <td className="num">{r.total_seconds?.toFixed(2) ?? '—'}</td>
                  <td className="num">{r.best_distance?.toFixed(4) ?? '—'}</td>
                  <td className="nowrap muted">{r.retrieved_chunk_ids}</td>
                  <td><FeedbackBadge value={r.feedback} /></td>
                </tr>
                {open === r.index && (
                  <tr className="expanded">
                    <td colSpan={8}>
                      <div className="answer">{r.answer}</div>
                      <div className="result-foot">
                        <span className="muted">Change rating:</span>
                        <FeedbackButtons value={r.feedback} onChange={(f) => void rate(r, f)} />
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {!rows.length && (
              <tr><td colSpan={8} className="muted">No log rows match.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
