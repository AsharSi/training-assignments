import { CATEGORIES } from '../data/events.js'

function EventFilters({ search, category, onSearchChange, onCategoryChange }) {
  return (
    <div className="filters">
      <label className="field search-field">
        <span>Search by title</span>
        <input
          type="search"
          placeholder="e.g. cloud, writing, visual…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </label>
      <div className="category-tabs" role="group" aria-label="Filter by category">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            type="button"
            className={c === category ? 'chip active' : 'chip'}
            aria-pressed={c === category}
            onClick={() => onCategoryChange(c)}
          >
            {c}
          </button>
        ))}
      </div>
    </div>
  )
}

export default EventFilters
