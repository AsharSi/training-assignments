import { Link } from 'react-router-dom'
import EmptyState from '../components/EmptyState.jsx'
import RegistrationItem from '../components/RegistrationItem.jsx'
import { EVENTS } from '../data/events.js'

const eventsById = Object.fromEntries(EVENTS.map((event) => [event.id, event]))

function RegistrationsPage({ registrations, onCancel }) {
  // Order by event date, then by when the registration was made.
  const sorted = [...registrations].sort((a, b) => {
    const ea = eventsById[a.eventId]
    const eb = eventsById[b.eventId]
    const byEvent = `${ea?.date} ${ea?.time}`.localeCompare(`${eb?.date} ${eb?.time}`)
    return byEvent || a.createdAt.localeCompare(b.createdAt)
  })

  return (
    <section>
      <div className="page-header">
        <h1>My registrations</h1>
        <p className="muted">
          {registrations.length === 1
            ? '1 active registration'
            : `${registrations.length} active registrations`}
        </p>
      </div>

      {sorted.length === 0 ? (
        <EmptyState title="No registrations yet" message="Registrations you make will appear here.">
          <Link to="/" className="btn btn-primary">
            Browse events
          </Link>
        </EmptyState>
      ) : (
        <>
          <div className="registration-header" aria-hidden="true">
            <span>Attendee</span>
            <span>Event</span>
            <span />
          </div>
          <ul className="registration-list">
            {sorted.map((registration) => (
              <RegistrationItem
                key={registration.id}
                registration={registration}
                event={eventsById[registration.eventId]}
                onCancel={onCancel}
              />
            ))}
          </ul>
        </>
      )}
    </section>
  )
}

export default RegistrationsPage
