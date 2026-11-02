import { useRef, useState } from 'react'
import { api } from '../api'
import { normQuestion } from '../stats'
import { newId } from '../storage'
import type { Feedback, RunJob as Job, SavedModel, SavedQuestion } from '../types'
import { FeedbackButtons } from './FeedbackButtons'
import { ResultsTable } from './ResultsTable'

interface Props {
  models: SavedModel[]
  setModels: (fn: (m: SavedModel[]) => SavedModel[]) => void
  setQuestions: (fn: (q: SavedQuestion[]) => SavedQuestion[]) => void
  questions: SavedQuestion[]
  defaultModel: string
  onLogged: () => void
}

export function RunPanel({ models, setModels, questions, setQuestions, defaultModel, onLogged }: Props) {
  const [selModels, setSelModels] = useState<Set<string>>(new Set())
  const [selQuestions, setSelQuestions] = useState<Set<string>>(new Set())
  const [adhoc, setAdhoc] = useState('')
  const [adhocModel, setAdhocModel] = useState('')
  const [topK, setTopK] = useState(3)
  const [repeats, setRepeats] = useState(1)
  const [jobs, setJobs] = useState<Job[]>([])
  const [running, setRunning] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const modelOptions = [...new Set([defaultModel, ...models.map((m) => m.name)].filter(Boolean))]

  const chosenModels = [
    ...modelOptions.filter((m) => selModels.has(m)),
    ...adhocModel.split(',').map((s) => s.trim()).filter(Boolean),
  ]
  const chosenQuestions = [
    ...questions.filter((q) => selQuestions.has(q.id)).map((q) => q.text),
    ...adhoc.split('\n').map((s) => s.trim()).filter(Boolean),
  ]
  const total = chosenModels.length * chosenQuestions.length * repeats

  const toggle = (set: Set<string>, value: string, update: (s: Set<string>) => void) => {
    const next = new Set(set)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    update(next)
  }

  /** Save the typed model slug(s) to the library and tick them. */
  const saveAdhocModels = () => {
    const names = [...new Set(adhocModel.split(',').map((s) => s.trim()).filter(Boolean))]
    if (!names.length) return
    setModels((ms) => {
      const known = new Set(ms.map((m) => m.name))
      return [...ms, ...names.filter((n) => !known.has(n)).map((name) => ({ id: newId(), name, note: '' }))]
    })
    setSelModels((s) => new Set([...s, ...names]))
    setAdhocModel('')
  }

  /** Save the typed question(s) to the library (skipping duplicates) and tick them. */
  const saveAdhocQuestions = () => {
    const lines = adhoc.split('\n').map((s) => s.trim()).filter(Boolean)
    if (!lines.length) return
    const byNorm = new Map(questions.map((q) => [normQuestion(q.text), q.id]))
    const fresh: SavedQuestion[] = []
    const ids: string[] = []
    for (const text of lines) {
      const k = normQuestion(text)
      let id = byNorm.get(k)
      if (!id) {
        id = newId()
        byNorm.set(k, id)
        fresh.push({ id, text, category: '' })
      }
      ids.push(id)
    }
    setQuestions((qs) => [...qs, ...fresh])
    setSelQuestions((s) => new Set([...s, ...ids]))
    setAdhoc('')
  }

  const patchJob = (key: string, patch: Partial<Job>) =>
    setJobs((js) => js.map((j) => (j.key === key ? { ...j, ...patch } : j)))

  const run = async () => {
    if (!total) return
    const list: Job[] = []
    for (let r = 0; r < repeats; r++)
      for (const question of chosenQuestions)
        for (const model of chosenModels)
          list.push({ key: newId(), model, question, status: 'queued' })
    setJobs(list)
    setRunning(true)
    const controller = new AbortController()
    abortRef.current = controller

    // Sequential on purpose: free OpenRouter models are rate-limited, and
    // parallel calls would distort the latency numbers we are measuring.
    for (const job of list) {
      if (controller.signal.aborted) break
      patchJob(job.key, { status: 'running' })
      try {
        const result = await api.ask(job.question, job.model, topK, controller.signal)
        patchJob(job.key, { status: 'done', result })
        onLogged()
      } catch (e) {
        if (controller.signal.aborted) {
          patchJob(job.key, { status: 'queued' })
          break
        }
        patchJob(job.key, { status: 'error', error: (e as Error).message })
      }
    }
    setRunning(false)
    abortRef.current = null
  }

  const rate = async (job: Job, feedback: Feedback) => {
    if (!job.result) return
    const prev = job.result.feedback
    patchJob(job.key, { result: { ...job.result, feedback } })
    try {
      await api.setFeedback(job.result.index, feedback)
      onLogged()
    } catch (e) {
      patchJob(job.key, { result: { ...job.result, feedback: prev }, error: (e as Error).message })
    }
  }

  const done = jobs.filter((j) => j.status === 'done' || j.status === 'error').length

  return (
    <div className="stack">
      <div className="grid-2">
        <section className="card">
          <h2>Models</h2>
          <div className="toolbar">
            <button className="ghost" onClick={() => setSelModels(new Set(modelOptions))}>All</button>
            <button className="ghost" onClick={() => setSelModels(new Set())}>None</button>
          </div>
          <div className="checks">
            {modelOptions.map((m) => (
              <label key={m} className="check">
                <input type="checkbox" checked={selModels.has(m)} onChange={() => toggle(selModels, m, setSelModels)} />
                <code>{m}</code>
                {m === defaultModel && <span className="tag">.env default</span>}
              </label>
            ))}
          </div>
          <div className="form-row">
            <input
              placeholder="Add model, e.g. openai/gpt-4o-mini (comma separated for several)"
              value={adhocModel}
              onChange={(e) => setAdhocModel(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && saveAdhocModels()}
            />
            <button className="primary" disabled={!adhocModel.trim()} onClick={saveAdhocModels}>Save</button>
          </div>
          <p className="muted small">Saved models are kept in this browser and ticked for this run.</p>
        </section>

        <section className="card">
          <h2>Questions</h2>
          <div className="toolbar">
            <button className="ghost" onClick={() => setSelQuestions(new Set(questions.map((q) => q.id)))}>All</button>
            <button className="ghost" onClick={() => setSelQuestions(new Set())}>None</button>
          </div>
          <div className="checks scroll">
            {questions.map((q) => (
              <label key={q.id} className="check">
                <input type="checkbox" checked={selQuestions.has(q.id)} onChange={() => toggle(selQuestions, q.id, setSelQuestions)} />
                <span>{q.text}</span>
                {q.category && <span className="tag">{q.category}</span>}
              </label>
            ))}
            {!questions.length && <p className="muted">Save questions in the Library tab, or type them below.</p>}
          </div>
          <textarea
            rows={3}
            placeholder="Add questions, one per line"
            value={adhoc}
            onChange={(e) => setAdhoc(e.target.value)}
          />
          <div className="form-row">
            <span className="muted small grow">Saved questions are kept in this browser and ticked for this run.</span>
            <button className="primary" disabled={!adhoc.trim()} onClick={saveAdhocQuestions}>Save</button>
          </div>
        </section>
      </div>

      <div className="card toolbar">
        <label className="inline">
          Top-k chunks
          <input type="number" min={1} max={10} value={topK} onChange={(e) => setTopK(Math.max(1, Math.min(10, Number(e.target.value) || 3)))} />
        </label>
        <label className="inline">
          Repeats
          <input type="number" min={1} max={10} value={repeats} onChange={(e) => setRepeats(Math.max(1, Math.min(10, Number(e.target.value) || 1)))} />
        </label>
        <span className="muted">
          {chosenModels.length} model(s) × {chosenQuestions.length} question(s) × {repeats} = <strong>{total}</strong> call(s)
        </span>
        <span className="spacer" />
        {running ? (
          <button className="danger" onClick={() => abortRef.current?.abort()}>Stop</button>
        ) : (
          <button className="primary" disabled={!total} onClick={() => void run()}>Run</button>
        )}
      </div>

      {jobs.length > 0 && (
        <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={jobs.length} aria-valuenow={done}>
          <div style={{ width: `${(done / jobs.length) * 100}%` }} />
          <span>{done} / {jobs.length}</span>
        </div>
      )}

      {jobs.map((job) => (
        <article key={job.key} className={`card result status-${job.status}`}>
          <header className="result-head">
            <code>{job.model}</code>
            <span className="muted">{job.status === 'running' ? 'Running…' : job.status === 'queued' ? 'Queued' : ''}</span>
            {job.result && (
              <span className="metrics">
                <span title="End-to-end response time">⏱ {job.result.total_seconds?.toFixed(2)}s</span>
                <span title="Retrieval time">🔎 {job.result.retrieval_seconds.toFixed(2)}s</span>
                <span title="Best (lowest) cosine distance">d {job.result.best_distance?.toFixed(4)}</span>
                <span className="muted">log #{job.result.index}</span>
              </span>
            )}
          </header>
          <p className="question">Q: {job.question}</p>
          {job.status === 'error' && <div className="notice error">{job.error}</div>}
          {job.result && (
            <>
              <div className="answer">{job.result.answer}</div>
              <details>
                <summary>Retrieved: {job.result.retrieved_chunk_ids}</summary>
                {job.result.matches.map((m) => (
                  <div key={m.id} className="chunk">
                    <div className="muted">
                      <code>{m.id}</code> · distance {m.distance.toFixed(4)} · {m.source}
                    </div>
                    <pre>{m.text}</pre>
                  </div>
                ))}
              </details>
              <div className="result-foot">
                <span className="muted">Was this answer correct?</span>
                <FeedbackButtons value={job.result.feedback} onChange={(f) => void rate(job, f)} />
              </div>
            </>
          )}
        </article>
      ))}

      {jobs.length > 0 && <ResultsTable jobs={jobs} onRate={(job, f) => void rate(job, f)} />}
    </div>
  )
}
