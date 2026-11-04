import { useMemo, useState, type ReactNode } from 'react'
import type { LogRow, SavedQuestion } from '../types'
import { fmtNum, fmtPct, fmtSec, groupBy, normQuestion, summarize, type GroupStats } from '../stats'

interface Props {
  logs: LogRow[]
  questions: SavedQuestion[]
}

type SortKey = 'key' | 'runs' | 'accuracy' | 'p50Seconds' | 'p95Seconds' | 'avgDistance' | 'notFoundRate'

// Sequential blue ramp (light → dark) for the accuracy heatmap.
const SEQ = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']

interface Tip {
  x: number
  y: number
  content: ReactNode
}

export function AnalysisPanel({ logs, questions }: Props) {
  const [excluded, setExcluded] = useState<Set<string>>(new Set())
  const [scope, setScope] = useState<'all' | 'saved'>('all')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: 'accuracy', dir: -1 })
  const [tip, setTip] = useState<Tip | null>(null)

  const allModels = useMemo(() => [...new Set(logs.map((r) => r.model))].sort(), [logs])
  const categoryOf = useMemo(() => {
    const m = new Map<string, string>()
    for (const q of questions) m.set(normQuestion(q.text), q.category)
    return m
  }, [questions])
  const categories = [...new Set(questions.map((q) => q.category).filter(Boolean))].sort()

  const rows = useMemo(
    () =>
      logs.filter((r) => {
        if (excluded.has(r.model)) return false
        const nq = normQuestion(r.question)
        if (scope === 'saved' && !categoryOf.has(nq)) return false
        if (category && categoryOf.get(nq) !== category) return false
        return true
      }),
    [logs, excluded, scope, category, categoryOf],
  )

  const overall = summarize('all', rows)
  const byModel = useMemo(() => {
    const list = [...groupBy(rows, (r) => r.model)].map(([k, rs]) => summarize(k, rs))
    return list.sort((a, b) => {
      const av = a[sort.key]
      const bv = b[sort.key]
      if (av == null) return 1
      if (bv == null) return -1
      return (av < bv ? -1 : av > bv ? 1 : 0) * sort.dir
    })
  }, [rows, sort])

  // Question × model matrix
  const qGroups = useMemo(() => {
    const g = groupBy(rows, (r) => normQuestion(r.question))
    return [...g].map(([k, rs]) => ({
      key: k,
      label: rs[rs.length - 1].question.trim(),
      overall: summarize(k, rs),
      cells: groupBy(rs, (r) => r.model),
    }))
      // Hardest questions first: lowest accuracy, unrated last.
      .sort((a, b) => (a.overall.accuracy ?? 2) - (b.overall.accuracy ?? 2) || b.overall.runs - a.overall.runs)
  }, [rows])
  const matrixModels = byModel.map((m) => m.key)

  const showTip = (e: React.MouseEvent, content: ReactNode) => setTip({ x: e.clientX, y: e.clientY, content })
  const hideTip = () => setTip(null)

  const header = (key: SortKey, label: string, num = true) => (
    <th
      className={`${num ? 'num' : ''} sortable`}
      aria-sort={sort.key === key ? (sort.dir === 1 ? 'ascending' : 'descending') : 'none'}
      onClick={() => setSort((s) => ({ key, dir: s.key === key ? ((-s.dir) as 1 | -1) : key === 'key' ? 1 : -1 }))}
    >
      {label}
      {sort.key === key ? (sort.dir === 1 ? ' ▲' : ' ▼') : ''}
    </th>
  )

  const maxP50 = Math.max(0, ...byModel.map((m) => m.p50Seconds ?? 0))

  if (!logs.length) return <div className="card muted">No log rows yet. Run some questions first.</div>

  return (
    <div className="stack" onMouseLeave={hideTip}>
      {/* Filters: one row above the charts */}
      <div className="card toolbar wrap">
        <span className="muted">Models:</span>
        {allModels.map((m) => (
          <button
            key={m}
            className={`chip ${excluded.has(m) ? '' : 'on'}`}
            aria-pressed={!excluded.has(m)}
            onClick={() =>
              setExcluded((s) => {
                const n = new Set(s)
                if (n.has(m)) n.delete(m)
                else n.add(m)
                return n
              })
            }
          >
            {m}
          </button>
        ))}
        <span className="spacer" />
        <select value={scope} onChange={(e) => setScope(e.target.value as 'all' | 'saved')} aria-label="Question scope">
          <option value="all">All questions in log</option>
          <option value="saved">Saved questions only</option>
        </select>
        {categories.length > 0 && (
          <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
            <option value="">All categories</option>
            {categories.map((c) => <option key={c}>{c}</option>)}
          </select>
        )}
      </div>

      <div className="tiles">
        <Tile label="Runs" value={String(overall.runs)} sub={`${byModel.length} model(s), ${qGroups.length} question(s)`} />
        <Tile label="Accuracy (rated)" value={fmtPct(overall.accuracy)} sub={`${overall.correct} correct / ${overall.correct + overall.incorrect} rated`} />
        <Tile label="Rated" value={fmtPct(overall.runs ? (overall.runs - overall.unrated) / overall.runs : null)} sub={`${overall.unrated} still not rated`} />
        <Tile label="Median response" value={fmtSec(overall.p50Seconds)} sub={`p95 ${fmtSec(overall.p95Seconds)}`} />
      </div>

      <div className="grid-3">
        <section className="card">
          <h3>Accuracy by model</h3>
          <p className="muted small">Correct ÷ rated answers</p>
          <div className="bars">
            {byModel.map((m) => (
              <BarRow
                key={m.key}
                label={m.key}
                value={fmtPct(m.accuracy)}
                segments={[{ frac: m.accuracy ?? 0, cls: 'bar-series' }]}
                onHover={(e) => showTip(e, <ModelTip s={m} />)}
                onLeave={hideTip}
              />
            ))}
          </div>
        </section>
        <section className="card">
          <h3>Median response time</h3>
          <p className="muted small">End-to-end seconds (retrieval + model)</p>
          <div className="bars">
            {byModel.map((m) => (
              <BarRow
                key={m.key}
                label={m.key}
                value={fmtSec(m.p50Seconds)}
                segments={[{ frac: maxP50 ? (m.p50Seconds ?? 0) / maxP50 : 0, cls: 'bar-series' }]}
                onHover={(e) => showTip(e, <ModelTip s={m} />)}
                onLeave={hideTip}
              />
            ))}
          </div>
        </section>
        <section className="card">
          <h3>Feedback mix</h3>
          <div className="legend">
            <span><i className="sw fb-correct-bg" /> ✓ Correct</span>
            <span><i className="sw fb-incorrect-bg" /> ✕ Incorrect</span>
            <span><i className="sw fb-not-rated-bg" /> – Not rated</span>
          </div>
          <div className="bars">
            {byModel.map((m) => (
              <BarRow
                key={m.key}
                label={m.key}
                value={String(m.runs)}
                segments={[
                  { frac: m.correct / m.runs, cls: 'fb-correct-bg' },
                  { frac: m.incorrect / m.runs, cls: 'fb-incorrect-bg' },
                  { frac: m.unrated / m.runs, cls: 'fb-not-rated-bg' },
                ]}
                onHover={(e) => showTip(e, <ModelTip s={m} />)}
                onLeave={hideTip}
              />
            ))}
          </div>
        </section>
      </div>

      <section className="card table-wrap">
        <h3>Model leaderboard</h3>
        <table className="table">
          <thead>
            <tr>
              {header('key', 'Model', false)}
              {header('runs', 'Runs')}
              <th className="num">✓ / ✕ / –</th>
              {header('accuracy', 'Accuracy')}
              {header('notFoundRate', '"Not found" rate')}
              {header('p50Seconds', 'p50 time')}
              {header('p95Seconds', 'p95 time')}
              {header('avgDistance', 'Avg best dist.')}
            </tr>
          </thead>
          <tbody>
            {byModel.map((m) => (
              <tr key={m.key}>
                <td><code>{m.key}</code></td>
                <td className="num">{m.runs}</td>
                <td className="num">{m.correct} / {m.incorrect} / {m.unrated}</td>
                <td className="num strong">{fmtPct(m.accuracy)}</td>
                <td className="num">{fmtPct(m.notFoundRate)}</td>
                <td className="num">{fmtSec(m.p50Seconds)}</td>
                <td className="num">{fmtSec(m.p95Seconds)}</td>
                <td className="num">{fmtNum(m.avgDistance, 4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card table-wrap">
        <h3>Question × model accuracy</h3>
        <div className="legend">
          <span className="muted small">Accuracy:</span>
          <span className="ramp">
            {SEQ.map((c) => <i key={c} style={{ background: c }} />)}
          </span>
          <span className="muted small">0% → 100% · grey = run but not rated · hardest questions first</span>
        </div>
        <table className="table heat">
          <thead>
            <tr>
              <th>Question</th>
              <th className="num">Overall</th>
              {matrixModels.map((m) => <th key={m} className="model-col"><code>{m}</code></th>)}
            </tr>
          </thead>
          <tbody>
            {qGroups.map((q) => (
              <tr key={q.key}>
                <td className="q-cell">
                  {q.label}
                  {categoryOf.get(q.key) && <span className="tag">{categoryOf.get(q.key)}</span>}
                </td>
                <td className="num strong">{fmtPct(q.overall.accuracy)}</td>
                {matrixModels.map((m) => {
                  const rs = q.cells.get(m)
                  if (!rs) return <td key={m} className="cell empty" />
                  const s = summarize(m, rs)
                  const step = s.accuracy == null ? -1 : Math.min(SEQ.length - 1, Math.floor(s.accuracy * SEQ.length))
                  return (
                    <td
                      key={m}
                      className={`cell ${step < 0 ? 'unrated' : step >= 3 ? 'on-dark' : ''}`}
                      style={step >= 0 ? { background: SEQ[step] } : undefined}
                      onMouseMove={(e) => showTip(e, <CellTip q={q.label} s={s} />)}
                      onMouseLeave={hideTip}
                    >
                      <span className="cell-main">{step < 0 ? 'n/r' : fmtPct(s.accuracy)}</span>
                      <span className="cell-sub">{s.runs}× · {fmtSec(s.p50Seconds)}</span>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {tip && (
        <div className="tooltip" style={{ left: tip.x + 14, top: tip.y + 14 }} role="tooltip">
          {tip.content}
        </div>
      )}
    </div>
  )
}

function Tile({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="card tile">
      <div className="tile-label">{label}</div>
      <div className="tile-value">{value}</div>
      <div className="muted small">{sub}</div>
    </div>
  )
}

function BarRow(props: {
  label: string
  value: string
  segments: { frac: number; cls: string }[]
  onHover: (e: React.MouseEvent) => void
  onLeave: () => void
}) {
  return (
    <div className="bar-row" onMouseMove={props.onHover} onMouseLeave={props.onLeave}>
      <div className="bar-label" title={props.label}>{props.label}</div>
      <div className="bar-track">
        {props.segments
          .filter((s) => s.frac > 0)
          .map((s, i) => (
            <div key={i} className={`bar-seg ${s.cls}`} style={{ width: `${s.frac * 100}%` }} />
          ))}
      </div>
      <div className="bar-value">{props.value}</div>
    </div>
  )
}

function ModelTip({ s }: { s: GroupStats }) {
  return (
    <>
      <div className="tip-title">{s.key}</div>
      <div>Runs: {s.runs}</div>
      <div>✓ {s.correct} · ✕ {s.incorrect} · – {s.unrated}</div>
      <div>Accuracy: {fmtPct(s.accuracy)}</div>
      <div>p50 {fmtSec(s.p50Seconds)} · p95 {fmtSec(s.p95Seconds)}</div>
      <div>Avg best distance: {fmtNum(s.avgDistance, 4)}</div>
    </>
  )
}

function CellTip({ q, s }: { q: string; s: GroupStats }) {
  return (
    <>
      <div className="tip-title">{s.key}</div>
      <div className="tip-q">{q}</div>
      <div>Runs: {s.runs} · ✓ {s.correct} · ✕ {s.incorrect} · – {s.unrated}</div>
      <div>Accuracy: {fmtPct(s.accuracy)}</div>
      <div>p50 {fmtSec(s.p50Seconds)} · avg dist {fmtNum(s.avgDistance, 4)}</div>
    </>
  )
}
