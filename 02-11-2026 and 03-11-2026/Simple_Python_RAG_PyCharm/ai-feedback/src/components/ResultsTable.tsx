import { Fragment, useMemo, useState } from 'react'
import { downloadCsv, fileStamp, type CsvColumn } from '../csv'
import type { Feedback, RunJob } from '../types'
import { FeedbackBadge, FeedbackButtons } from './FeedbackButtons'

interface Props {
  jobs: RunJob[]
  onRate: (job: RunJob, f: Feedback) => void
}

const STATUS_LABEL: Record<RunJob['status'], string> = {
  queued: 'Queued',
  running: 'Running…',
  done: 'Done',
  error: 'Error',
}

const COLUMNS: CsvColumn<RunJob>[] = [
  { header: 'log_index', value: (j) => j.result?.index },
  { header: 'timestamp', value: (j) => j.result?.timestamp },
  { header: 'model', value: (j) => j.model },
  { header: 'question', value: (j) => j.question },
  { header: 'status', value: (j) => j.status },
  { header: 'answer', value: (j) => j.result?.answer ?? j.error },
  { header: 'retrieved_chunk_ids', value: (j) => j.result?.retrieved_chunk_ids },
  { header: 'best_distance', value: (j) => j.result?.best_distance },
  { header: 'retrieval_seconds', value: (j) => j.result?.retrieval_seconds },
  { header: 'total_seconds', value: (j) => j.result?.total_seconds },
  { header: 'feedback', value: (j) => j.result?.feedback },
]

/** Table of the current run's results, with filters and CSV export. */
export function ResultsTable({ jobs, onRate }: Props) {
  const [model, setModel] = useState('')
  const [status, setStatus] = useState('')
  const [feedback, setFeedback] = useState('')
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState<string | null>(null)

  const models = useMemo(() => [...new Set(jobs.map((j) => j.model))].sort(), [jobs])
  const rows = useMemo(() => {
    const s = search.trim().toLowerCase()
    return jobs.filter(
      (j) =>
        (!model || j.model === model) &&
        (!status || j.status === status) &&
        (!feedback || j.result?.feedback === feedback) &&
        (!s || j.question.toLowerCase().includes(s) || (j.result?.answer ?? j.error ?? '').toLowerCase().includes(s)),
    )
  }, [jobs, model, status, feedback, search])

  return (
    <section className="card stack">
      <h2>Results table</h2>
      <div className="toolbar">
        <select value={model} onChange={(e) => setModel(e.target.value)} aria-label="Filter by model">
          <option value="">All models</option>
          {models.map((m) => <option key={m}>{m}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
          <option value="">All statuses</option>
          <option value="done">Done</option>
          <option value="error">Error</option>
          <option value="running">Running</option>
          <option value="queued">Queued</option>
        </select>
        <select value={feedback} onChange={(e) => setFeedback(e.target.value)} aria-label="Filter by feedback">
          <option value="">All feedback</option>
          <option>Correct</option>
          <option>Incorrect</option>
          <option>Not rated</option>
        </select>
        <input className="grow" placeholder="Search question or answer…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <span className="muted">{rows.length} of {jobs.length}</span>
        <button disabled={!rows.length} onClick={() => downloadCsv(`run-results_${fileStamp()}.csv`, rows, COLUMNS)}>
          Export CSV
        </button>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Log #</th>
              <th>Model</th>
              <th>Question</th>
              <th>Status</th>
              <th>Answer</th>
              <th className="num">Total s</th>
              <th className="num">Retrieval s</th>
              <th className="num">Best dist.</th>
              <th>Chunks</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((j) => (
              <Fragment key={j.key}>
                <tr className="clickable" onClick={() => setOpen(open === j.key ? null : j.key)} aria-expanded={open === j.key}>
                  <td className="muted">{j.result?.index ?? '—'}</td>
                  <td><code>{j.model}</code></td>
                  <td>{j.question}</td>
                  <td className={`nowrap ${j.status === 'error' ? 'text-error' : ''}`}>{STATUS_LABEL[j.status]}</td>
                  <td><div className="answer-cell">{j.result?.answer ?? j.error ?? ''}</div></td>
                  <td className="num">{j.result?.total_seconds?.toFixed(2) ?? '—'}</td>
                  <td className="num">{j.result?.retrieval_seconds.toFixed(2) ?? '—'}</td>
                  <td className="num">{j.result?.best_distance?.toFixed(4) ?? '—'}</td>
                  <td className="nowrap muted">{j.result?.retrieved_chunk_ids ?? ''}</td>
                  <td>{j.result ? <FeedbackBadge value={j.result.feedback} /> : '—'}</td>
                </tr>
                {open === j.key && (
                  <tr className="expanded">
                    <td colSpan={10}>
                      <div className="answer">{j.result?.answer ?? j.error ?? 'No answer yet.'}</div>
                      {j.result && (
                        <div className="result-foot">
                          <span className="muted">Rate:</span>
                          <FeedbackButtons value={j.result.feedback} onChange={(f) => onRate(j, f)} />
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {!rows.length && (
              <tr><td colSpan={10} className="muted">No results match the filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
