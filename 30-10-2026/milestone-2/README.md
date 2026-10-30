# Event Enrollment Manager

A responsive React + Vite single-page app for a community learning centre. Visitors can browse upcoming events, register for an available seat, view registrations and cancel them. It is **frontend only**: event data lives in a JavaScript file and registrations are stored in the browser's `localStorage`.

## Requirements

- Node.js 20.19+ (or 22.12+)
- npm

## Installation and start

```bash
npm install        # install dependencies
npm run dev        # start the dev server (http://localhost:5173)
```

Other scripts:

```bash
npm run build      # production build into dist/
npm run preview    # serve the production build locally
npm run lint       # lint with oxlint
```

## Features

- **Events page (`/`)**: all six events shown as cards with title, category, date, time, total seats and available seats.
  - Case-insensitive title search.
  - Category filter: All, Technology, Arts, Life Skills.
  - Empty-state message (with a "Clear filters" button) when nothing matches.
  - Fully booked events show a disabled **Fully booked** button.
- **Registration form** (opens in a dialog from **Register**):
  - Full name and email are required; email format is validated.
  - The same email cannot register twice for the same event (trimmed, case-insensitive); it can register for other events.
  - Registration is blocked when no seats are left.
  - A confirmation message is shown and the seat count updates immediately.
- **Registrations page (`/registrations`)**: attendee name, email, event title and event date/time, with a **Cancel** action that asks for confirmation and frees the seat.
- **Persistence**: registrations are saved to `localStorage` (key `event-enrollment.registrations`) and survive refresh. Available seats are always computed as `capacity − active registrations`, so they stay correct after reload.

To reset the app to its initial state, clear the key above from DevTools → Application → Local Storage (or run `localStorage.clear()` in the console).

## Project structure

```
src/
├── data/events.js              # starter event dataset + categories
├── hooks/useRegistrations.js   # registration state, localStorage sync, seat counts
├── utils/format.js             # date/time formatting, email helpers
├── components/
│   ├── Navbar.jsx              # top navigation (NavLink)
│   ├── EventFilters.jsx        # search box + category chips
│   ├── EventCard.jsx           # single event card with Register button
│   ├── RegistrationForm.jsx    # dialog form with validation + confirmation
│   ├── RegistrationItem.jsx    # registration row with confirm-to-cancel
│   └── EmptyState.jsx          # reusable empty-state message
├── pages/
│   ├── EventsPage.jsx
│   ├── RegistrationsPage.jsx
│   └── NotFoundPage.jsx
├── App.jsx                     # routes + shared registration state
├── main.jsx                    # entry point, BrowserRouter
└── index.css                   # styles (plain CSS, responsive)
```

## State design

- `useRegistrations` owns the only mutable state: an array of `{ id, eventId, name, email, createdAt }`. It initialises lazily from `localStorage` and writes back in a `useEffect` whenever the array changes.
- Updates are immutable (`[...prev, item]` to add, `prev.filter(...)` to cancel).
- Seat availability is derived (`useMemo` counts per event) rather than stored, so it can never drift from the registrations list.
- Lists use stable keys (`event.id`, `registration.id`).

## Tech stack

React 19, Vite, React Router, plain CSS, browser `localStorage`.
