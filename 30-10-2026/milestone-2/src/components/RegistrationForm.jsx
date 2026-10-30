import { useEffect, useRef, useState } from 'react'
import { formatDate, formatTime, isValidEmail } from '../utils/format.js'

const EMPTY_FORM = { name: '', email: '' }

function validate(values, available, isEmailRegistered) {
  const errors = {}
  if (!values.name.trim()) {
    errors.name = 'Full name is required.'
  }
  if (!values.email.trim()) {
    errors.email = 'Email address is required.'
  } else if (!isValidEmail(values.email)) {
    errors.email = 'Enter a valid email address, e.g. name@example.com.'
  } else if (isEmailRegistered(values.email)) {
    errors.email = 'This email is already registered for this event.'
  }
  if (available <= 0) {
    errors.form = 'Sorry, this event is fully booked.'
  }
  return errors
}

function RegistrationForm({ event, available, isEmailRegistered, onSubmit, onClose }) {
  const [values, setValues] = useState(EMPTY_FORM)
  const [errors, setErrors] = useState({})
  const [confirmation, setConfirmation] = useState(null)
  const nameRef = useRef(null)

  useEffect(() => {
    nameRef.current?.focus()
  }, [])

  useEffect(() => {
    function handleKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  function handleChange(e) {
    const { name, value } = e.target
    setValues((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    const found = validate(values, available, isEmailRegistered)
    setErrors(found)
    if (Object.keys(found).length > 0) return

    const registration = onSubmit(values.name, values.email)
    setConfirmation(registration)
    setValues(EMPTY_FORM)
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="register-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="modal-close" aria-label="Close" onClick={onClose}>
          ×
        </button>
        <h2 id="register-title">Register for {event.title}</h2>
        <p className="muted">
          {formatDate(event.date)} at {formatTime(event.date, event.time)} ·{' '}
          <strong>{available}</strong> of {event.seats} seats available
        </p>

        {confirmation ? (
          <div className="alert alert-success" role="status">
            <p>
              <strong>You're registered!</strong> {confirmation.name} ({confirmation.email}) has a
              seat at {event.title}.
            </p>
            <div className="form-actions">
              <button type="button" className="btn btn-primary" onClick={onClose}>
                Done
              </button>
              {available > 0 && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setConfirmation(null)}
                >
                  Register someone else
                </button>
              )}
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            {errors.form && (
              <div className="alert alert-error" role="alert">
                {errors.form}
              </div>
            )}
            <label className="field">
              <span>Full name *</span>
              <input
                ref={nameRef}
                name="name"
                type="text"
                autoComplete="name"
                value={values.name}
                onChange={handleChange}
                aria-invalid={Boolean(errors.name)}
                aria-describedby={errors.name ? 'name-error' : undefined}
              />
              {errors.name && (
                <small id="name-error" className="field-error">
                  {errors.name}
                </small>
              )}
            </label>
            <label className="field">
              <span>Email address *</span>
              <input
                name="email"
                type="email"
                autoComplete="email"
                value={values.email}
                onChange={handleChange}
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? 'email-error' : undefined}
              />
              {errors.email && (
                <small id="email-error" className="field-error">
                  {errors.email}
                </small>
              )}
            </label>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={available <= 0}>
                Confirm registration
              </button>
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default RegistrationForm
