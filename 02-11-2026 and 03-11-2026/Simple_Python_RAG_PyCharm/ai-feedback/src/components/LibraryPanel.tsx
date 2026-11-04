import { useRef, useState } from 'react'
import { newId } from '../storage'
import type { LogRow, SavedModel, SavedQuestion } from '../types'
import { normQuestion } from '../stats'

interface Props {
  models: SavedModel[]
  setModels: (fn: (m: SavedModel[]) => SavedModel[]) => void
  questions: SavedQuestion[]
  setQuestions: (fn: (q: SavedQuestion[]) => SavedQuestion[]) => void
  logs: LogRow[]
}

export function LibraryPanel({ models, setModels, questions, setQuestions, logs }: Props) {
  const [modelName, setModelName] = useState('')
  const [modelNote, setModelNote] = useState('')
  const [qText, setQText] = useState('')
  const [qCategory, setQCategory] = useState('')
  const [message, setMessage] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const addModel = () => {
    const name = modelName.trim()
    if (!name) return
    if (models.some((m) => m.name === name)) return setMessage(`Model "${name}" is already saved.`)
    setModels((ms) => [...ms, { id: newId(), name, note: modelNote.trim() }])
    setModelName('')
    setModelNote('')
    setMessage('')
  }

  const addQuestions = () => {
    // One question per line so a whole test set can be pasted at once.
    const lines = qText.split('\n').map((l) => l.trim()).filter(Boolean)
    if (!lines.length) return
    const existing = new Set(questions.map((q) => normQuestion(q.text)))
    const fresh = lines.filter((l) => !existing.has(normQuestion(l)))
    setQuestions((qs) => [...qs, ...fresh.map((text) => ({ id: newId(), text, category: qCategory.trim() }))])
    setQText('')
    setMessage(`Added ${fresh.length} question(s)${fresh.length < lines.length ? `, skipped ${lines.length - fresh.length} duplicate(s)` : ''}.`)
  }

  const importFromLogs = () => {
    const knownModels = new Set(models.map((m) => m.name))
    const newModels = [...new Set(logs.map((r) => r.model))].filter((m) => m && !knownModels.has(m))
    const knownQs = new Set(questions.map((q) => normQuestion(q.text)))
    const seen = new Set<string>()
    const newQs: string[] = []
    for (const r of logs) {
      const k = normQuestion(r.question)
      if (r.question && !knownQs.has(k) && !seen.has(k)) {
        seen.add(k)
        newQs.push(r.question.trim())
      }
    }
    setModels((ms) => [...ms, ...newModels.map((name) => ({ id: newId(), name, note: 'from log' }))])
    setQuestions((qs) => [...qs, ...newQs.map((text) => ({ id: newId(), text, category: 'from log' }))])
    setMessage(`Imported ${newModels.length} model(s) and ${newQs.length} question(s) from the log.`)
  }

  const exportJson = () => {
    const blob = new Blob([JSON.stringify({ models, questions }, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'ai-feedback-library.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const importJson = async (file: File) => {
    try {
      const data = JSON.parse(await file.text()) as { models?: SavedModel[]; questions?: SavedQuestion[] }
      const ms = (data.models ?? []).filter((m) => m?.name)
      const qs = (data.questions ?? []).filter((q) => q?.text)
      setModels((cur) => {
        const known = new Set(cur.map((m) => m.name))
        return [...cur, ...ms.filter((m) => !known.has(m.name)).map((m) => ({ id: newId(), name: m.name, note: m.note ?? '' }))]
      })
      setQuestions((cur) => {
        const known = new Set(cur.map((q) => normQuestion(q.text)))
        return [...cur, ...qs.filter((q) => !known.has(normQuestion(q.text))).map((q) => ({ id: newId(), text: q.text, category: q.category ?? '' }))]
      })
      setMessage(`Imported library file "${file.name}".`)
    } catch {
      setMessage('That file is not a valid library JSON.')
    }
  }

  return (
    <div className="stack">
      <div className="toolbar">
        <span className="muted">Saved in this browser (localStorage).</span>
        <span className="spacer" />
        <button onClick={importFromLogs} disabled={!logs.length}>Import from log</button>
        <button onClick={exportJson}>Export JSON</button>
        <button onClick={() => fileRef.current?.click()}>Import JSON</button>
        <input
          ref={fileRef}
          type="file"
          accept="application/json"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) void importJson(f)
            e.target.value = ''
          }}
        />
      </div>
      {message && <div className="notice">{message}</div>}

      <div className="grid-2">
        <section className="card">
          <h2>Models <span className="count">{models.length}</span></h2>
          <div className="form-row">
            <input
              placeholder="OpenRouter slug, e.g. openai/gpt-4o-mini"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addModel()}
            />
            <input placeholder="Note (optional)" value={modelNote} onChange={(e) => setModelNote(e.target.value)} />
            <button className="primary" onClick={addModel}>Save</button>
          </div>
          <ul className="list">
            {models.map((m) => (
              <li key={m.id}>
                <div className="grow">
                  <code>{m.name}</code>
                  {m.note && <span className="muted"> · {m.note}</span>}
                </div>
                <button className="ghost" onClick={() => setModels((ms) => ms.filter((x) => x.id !== m.id))} aria-label={`Delete ${m.name}`}>
                  Delete
                </button>
              </li>
            ))}
            {!models.length && <li className="muted">No models saved yet.</li>}
          </ul>
        </section>

        <section className="card">
          <h2>Questions <span className="count">{questions.length}</span></h2>
          <textarea
            rows={4}
            placeholder={'One question per line, e.g.\nWhat is the annual travel allowance?\nHow many days of annual leave do I get?'}
            value={qText}
            onChange={(e) => setQText(e.target.value)}
          />
          <div className="form-row">
            <input placeholder="Category (optional), e.g. travel" value={qCategory} onChange={(e) => setQCategory(e.target.value)} />
            <button className="primary" onClick={addQuestions}>Save</button>
          </div>
          <ul className="list">
            {questions.map((q) => (
              <li key={q.id}>
                <div className="grow">
                  {q.text}
                  {q.category && <span className="tag">{q.category}</span>}
                </div>
                <button className="ghost" onClick={() => setQuestions((qs) => qs.filter((x) => x.id !== q.id))} aria-label="Delete question">
                  Delete
                </button>
              </li>
            ))}
            {!questions.length && <li className="muted">No questions saved yet.</li>}
          </ul>
        </section>
      </div>
    </div>
  )
}
