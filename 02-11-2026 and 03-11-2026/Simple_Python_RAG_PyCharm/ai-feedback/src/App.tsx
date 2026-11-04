import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { AnalysisPanel } from './components/AnalysisPanel'
import { LibraryPanel } from './components/LibraryPanel'
import { LogsPanel } from './components/LogsPanel'
import { RunPanel } from './components/RunPanel'
import { useLocalStorage } from './storage'
import type { Health, LogRow, SavedModel, SavedQuestion } from './types'

type Tab = 'run' | 'logs' | 'analysis' | 'library'
const TABS: { id: Tab; label: string }[] = [
  { id: 'run', label: 'Ask & Rate' },
  { id: 'logs', label: 'Logs' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'library', label: 'Library' },
]
// A #logs / #analysis / #library hash in the URL opens that tab on load.
const HASH_TAB = TABS.find((t) => `#${t.id}` === window.location.hash)?.id

const byText = (a: string, b: string) => a.localeCompare(b, undefined, { sensitivity: 'base' })
const sortModels = (ms: SavedModel[]) => [...ms].sort((a, b) => byText(a.name, b.name))
const sortQuestions = (qs: SavedQuestion[]) => [...qs].sort((a, b) => byText(a.text.trim(), b.text.trim()))

export default function App() {
  const [tab, setTab] = useLocalStorage<Tab>('tab', 'run', { override: HASH_TAB })
  // Models stay sorted A→Z: what's already in storage is sorted on load, and every
  // save path (Ask & Rate, Library, imports) goes through setModels below.
  const [models, setStoredModels] = useLocalStorage<SavedModel[]>('models', [], { normalize: sortModels })
  const setModels = useCallback(
    (fn: (m: SavedModel[]) => SavedModel[]) => setStoredModels((ms) => sortModels(fn(ms))),
    [setStoredModels],
  )
  // Questions stay sorted A→Z the same way.
  const [questions, setStoredQuestions] = useLocalStorage<SavedQuestion[]>('questions', [], { normalize: sortQuestions })
  const setQuestions = useCallback(
    (fn: (q: SavedQuestion[]) => SavedQuestion[]) => setStoredQuestions((qs) => sortQuestions(fn(qs))),
    [setStoredQuestions],
  )
  const [health, setHealth] = useState<Health | null>(null)
  const [backendError, setBackendError] = useState('')
  const [logs, setLogs] = useState<LogRow[]>([])
  const [loading, setLoading] = useState(false)

  const refreshLogs = useCallback(async () => {
    setLoading(true)
    try {
      setLogs(await api.logs())
      setBackendError('')
    } catch (e) {
      setBackendError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    api.health().then(setHealth).catch((e: Error) => setBackendError(e.message))
    void refreshLogs()
  }, [refreshLogs])

  return (
    <div className="app">
      <header className="top">
        <div>
          <h1>RAG AI Feedback</h1>
          <p className="muted small">
            Ask the employee-guide RAG with different models, rate answers, and compare them.
            {health && <> Logging to <code>rag_feedback.csv</code>.</>}
          </p>
        </div>
        <span className={`status ${health ? 'ok' : 'down'}`}>
          <span aria-hidden="true">{health ? '●' : '○'}</span> {health ? 'Backend connected' : 'Backend offline'}
        </span>
      </header>

      {backendError && (
        <div className="notice error">
          {backendError}
          <div className="small">
            Start it with: <code>.venv\Scripts\python.exe -m uvicorn feedback_api:app --reload --port 8000</code>
          </div>
        </div>
      )}
      {health && !health.has_api_key && <div className="notice error">OPENAI_API_KEY is missing from the backend's .env file.</div>}

      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>
            {t.label}
            {t.id === 'logs' && <span className="count">{logs.length}</span>}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'run' && (
          <RunPanel models={models} setModels={setModels} questions={questions} setQuestions={setQuestions} defaultModel={health?.default_model ?? ''} onLogged={() => void refreshLogs()} />
        )}
        {tab === 'logs' && <LogsPanel logs={logs} setLogs={setLogs} onRefresh={() => void refreshLogs()} loading={loading} />}
        {tab === 'analysis' && <AnalysisPanel logs={logs} questions={questions} />}
        {tab === 'library' && (
          <LibraryPanel models={models} setModels={setModels} questions={questions} setQuestions={setQuestions} logs={logs} />
        )}
      </main>
    </div>
  )
}
