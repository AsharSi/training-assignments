import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'

const EXAMPLES = [
  'Find books related to Python programming.',
  'Is Python Crash Course available?',
  'Reserve Python Crash Course for Ahmed.',
  'Show me books related to artificial intelligence.',
  'Reserve a book that has no available copies.',
]

async function api(path, body) {
  const res = await fetch(`/api${path}`, body === undefined ? {} : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`)
  return data
}

function formatArgs(args) {
  return Object.entries(args || {})
    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    .join(', ')
}

function summarize(step) {
  const r = step.result || {}
  if (r.error) return `error: ${r.error}`
  if (step.tool === 'search_books') return `${r.match_count} match${r.match_count === 1 ? '' : 'es'}`
  if (step.tool === 'reserve_book') {
    return r.reserved ? `reserved ${r.reservation.reservation_id}` : `not reserved: ${r.reason}`
  }
  return 'done'
}

function ToolSteps({ steps }) {
  if (!steps?.length) return null
  return (
    <ul className="steps">
      {steps.map((s, i) => (
        <li key={i} className={s.result?.reserved === false || s.result?.error ? 'warn' : ''}>
          <code>{s.tool}({formatArgs(s.args)})</code>
          <span>→ {summarize(s)}</span>
        </li>
      ))}
    </ul>
  )
}

function ApprovalCard({ approval, busy, onDecide }) {
  const { book, customer_name } = approval
  return (
    <div className="approval">
      <div className="approval-title">Reservation approval required</div>
      <dl>
        <dt>Book</dt>
        <dd>{book ? `${book.title} (ID ${book.id})` : 'Unknown'}</dd>
        {book && (<><dt>Author</dt><dd>{book.author}</dd></>)}
        <dt>Customer</dt>
        <dd>{customer_name}</dd>
        {book && (<><dt>Copies</dt><dd>{book.available_copies} available</dd></>)}
      </dl>
      <div className="approval-actions">
        <button className="primary" disabled={busy} onClick={() => onDecide(true)}>Confirm</button>
        <button disabled={busy} onClick={() => onDecide(false)}>Decline</button>
      </div>
    </div>
  )
}

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [approval, setApproval] = useState(null)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [books, setBooks] = useState([])
  const [reservations, setReservations] = useState([])
  const [backendError, setBackendError] = useState(null)
  const endRef = useRef(null)

  const refreshData = useCallback(async () => {
    try {
      const [b, r] = await Promise.all([api('/books'), api('/reservations')])
      setBooks(b)
      setReservations(r)
      setBackendError(null)
    } catch {
      setBackendError('Cannot reach the backend. Start it with: uvicorn server:app --port 8000')
    }
  }, [])

  useEffect(() => { refreshData() }, [refreshData])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, approval, busy])

  function handleResult(data) {
    setSessionId(data.session_id)
    if (data.status === 'needs_approval') {
      setMessages((m) => [...m, { role: 'assistant', steps: data.steps, text: null }])
      setApproval(data.approval)
    } else {
      setMessages((m) => [...m, { role: 'assistant', steps: data.steps, text: data.reply }])
      setApproval(null)
    }
  }

  async function run(fn) {
    setBusy(true)
    try {
      handleResult(await fn())
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: err.message }])
    } finally {
      setBusy(false)
      refreshData()
    }
  }

  function send(text) {
    const message = (text ?? input).trim()
    if (!message || busy || approval) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text: message }])
    run(() => api('/chat', { session_id: sessionId, message }))
  }

  function decide(approved) {
    setMessages((m) => [...m, { role: 'user', text: approved ? 'Confirmed reservation.' : 'Declined reservation.' }])
    setApproval(null)
    run(() => api('/approve', { session_id: sessionId, approved }))
  }

  async function newChat() {
    if (sessionId) await api('/reset', { session_id: sessionId }).catch(() => {})
    setSessionId(null)
    setMessages([])
    setApproval(null)
  }

  return (
    <div className="layout">
      <main className="chat">
        <header className="chat-header">
          <div>
            <h1>Library Assistant</h1>
            <p>Searches the catalogue and reserves books, with your approval.</p>
          </div>
          <button onClick={newChat} disabled={busy}>New chat</button>
        </header>

        <div className="messages">
          {backendError && <div className="msg error">{backendError}</div>}

          {messages.length === 0 && (
            <div className="empty">
              <p>Try one of these:</p>
              <div className="examples">
                {EXAMPLES.map((e) => (
                  <button key={e} onClick={() => send(e)} disabled={busy}>{e}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.role === 'assistant' && <ToolSteps steps={m.steps} />}
              {m.text && <div className="text">{m.text}</div>}
            </div>
          ))}

          {approval && <ApprovalCard approval={approval} busy={busy} onDecide={decide} />}
          {busy && <div className="msg assistant thinking">Thinking…</div>}
          <div ref={endRef} />
        </div>

        <form className="composer" onSubmit={(e) => { e.preventDefault(); send() }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={approval ? 'Confirm or decline the reservation above' : 'Ask about books or reserve one…'}
            disabled={busy || !!approval}
            autoFocus
          />
          <button className="primary" type="submit" disabled={busy || !!approval || !input.trim()}>Send</button>
        </form>
      </main>

      <aside className="sidebar">
        <section>
          <h2>Catalogue</h2>
          <ul className="books">
            {books.map((b) => (
              <li key={b.id}>
                <div className="book-title">{b.title}</div>
                <div className="book-meta">
                  <span>#{b.id} · {b.author}</span>
                  <span className={`badge ${b.available_copies > 0 ? 'ok' : 'none'}`}>
                    {b.available_copies > 0 ? `${b.available_copies} left` : 'none'}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2>Reservations</h2>
          {reservations.length === 0 ? (
            <p className="muted">No reservations yet.</p>
          ) : (
            <ul className="reservations">
              {[...reservations].reverse().map((r) => (
                <li key={r.reservation_id}>
                  <div className="book-title">{r.title}</div>
                  <div className="book-meta">
                    <span>{r.customer_name}</span>
                    <span className="muted">{r.reservation_id}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </aside>
    </div>
  )
}
