import { formatDate, formatTime } from '../utils/format.js'

function EventCard({ event, available, onRegister }) {
  const isFull = available <= 0
  const categoryClass = `tag tag-${event.category.toLowerCase().replace(/\s+/g, '-')}`

  return (
    <article className={isFull ? 'event-card full' : 'event-card'}>
      <div className="event-card-head">
        <span className={categoryClass}>{event.category}</span>
        <span className="event-id">{event.id}</span>
      </div>
      <h3>{event.title}</h3>
      <dl className="event-meta">
        <div>
          <dt>Date</dt>
          <dd>{formatDate(event.date)}</dd>
        </div>
        <div>
          <dt>Time</dt>
          <dd>{formatTime(event.date, event.time)}</dd>
        </div>
        <div>
          <dt>Total seats</dt>
          <dd>{event.seats}</dd>
        </div>
        <div>
          <dt>Available</dt>
          <dd className={isFull ? 'seats-none' : 'seats-ok'}>{available}</dd>
        </div>
      </dl>
      <button
        type="button"
        className="btn btn-primary"
        disabled={isFull}
        onClick={() => onRegister(event)}
      >
        {isFull ? 'Fully booked' : 'Register'}
      </button>
    </article>
  )
}

export default EventCard
