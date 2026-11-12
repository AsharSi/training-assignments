import { useCallback, useState } from 'react'
import EmptyState from '../components/EmptyState.jsx'
import EventCard from '../components/EventCard.jsx'
import EventFilters from '../components/EventFilters.jsx'
import RegistrationForm from '../components/RegistrationForm.jsx'
import { EVENTS } from '../data/events.js'

function EventsPage({ bookedCounts, isEmailRegistered, onRegister }) {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All')
  const [selectedEvent, setSelectedEvent] = useState(null)

  const availableFor = (event) => Math.max(event.seats - (bookedCounts[event.id] ?? 0), 0)

  const query = search.trim().toLowerCase()
  const visibleEvents = EVENTS.filter(
    (event) =>
      (category === 'All' || event.category === category) &&
      event.title.toLowerCase().includes(query),
  )

  const closeForm = useCallback(() => setSelectedEvent(null), [])

  function resetFilters() {
    setSearch('')
    setCategory('All')
  }

  return (
    <section>
      <div className="page-header">
        <h1>Upcoming events</h1>
        <p className="muted">Browse short events and reserve your seat.</p>
      </div>

      <EventFilters
        search={search}
        category={category}
        onSearchChange={setSearch}
        onCategoryChange={setCategory}
      />

      <p className="result-count" aria-live="polite">
        Showing {visibleEvents.length} of {EVENTS.length} events
      </p>

      {visibleEvents.length === 0 ? (
        <EmptyState
          title="No events found"
          message={`No events match${query ? ` "${search.trim()}"` : ''}${
            category !== 'All' ? ` in ${category}` : ''
          }. Try a different search or category.`}
        >
          <button type="button" className="btn btn-secondary" onClick={resetFilters}>
            Clear filters
          </button>
        </EmptyState>
      ) : (
        <div className="event-grid">
          {visibleEvents.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              available={availableFor(event)}
              onRegister={setSelectedEvent}
            />
          ))}
        </div>
      )}

      {selectedEvent && (
        <RegistrationForm
          key={selectedEvent.id}
          event={selectedEvent}
          available={availableFor(selectedEvent)}
          isEmailRegistered={(email) => isEmailRegistered(selectedEvent.id, email)}
          onSubmit={(name, email) => onRegister(selectedEvent.id, name, email)}
          onClose={closeForm}
        />
      )}
    </section>
  )
}

export default EventsPage
