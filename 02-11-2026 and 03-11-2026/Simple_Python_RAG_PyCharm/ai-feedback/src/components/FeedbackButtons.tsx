import type { Feedback } from '../types'

interface Props {
  value: Feedback
  onChange: (f: Feedback) => void
  disabled?: boolean
}

const OPTIONS: { value: Feedback; label: string; icon: string }[] = [
  { value: 'Correct', label: 'Correct', icon: '✓' },
  { value: 'Incorrect', label: 'Incorrect', icon: '✕' },
  { value: 'Not rated', label: 'Skip', icon: '–' },
]

export function FeedbackButtons({ value, onChange, disabled }: Props) {
  return (
    <div className="seg" role="group" aria-label="Was this answer correct?">
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          className={`seg-btn fb-${o.value.replace(' ', '-').toLowerCase()} ${value === o.value ? 'active' : ''}`}
          aria-pressed={value === o.value}
          disabled={disabled}
          onClick={() => onChange(o.value)}
        >
          <span aria-hidden="true">{o.icon}</span> {o.label}
        </button>
      ))}
    </div>
  )
}

export function FeedbackBadge({ value }: { value: Feedback }) {
  const icon = value === 'Correct' ? '✓' : value === 'Incorrect' ? '✕' : '–'
  return (
    <span className={`badge fb-${value.replace(' ', '-').toLowerCase()}`}>
      <span aria-hidden="true">{icon}</span> {value}
    </span>
  )
}
