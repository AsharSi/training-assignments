import { useState } from 'react'
import { formatDate, formatTime } from '../utils/format.js'

function RegistrationItem({ registration, event, onCancel }) {
  const [confirming, setConfirming] = useState(false)

  return (
    <li className="registration-item">
      <div className="registration-info">
        <p className="registration-name">{registration.name}</p>
        <p className="muted">{registration.email}</p>
      </div>
      <div className="registration-event">
        <p>{event ? event.title : 'Unknown event'}</p>
        <p className="muted">
          {event ? `${formatDate(event.date)} · ${formatTime(event.date, event.time)}` : '—'}
        </p>
      </div>
      <div className="registration-actions">
        {confirming ? (
          <>
            <span className="confirm-text">Cancel this registration?</span>
            <button type="button" className="btn btn-danger" onClick={() => onCancel(registration.id)}>
              Yes, cancel
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => setConfirming(false)}>
              Keep
            </button>
          </>
        ) : (
          <button type="button" className="btn btn-outline-danger" onClick={() => setConfirming(true)}>
            Cancel
          </button>
        )}
      </div>
    </li>
  )
}

export default RegistrationItem
