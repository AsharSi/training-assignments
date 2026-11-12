import { useEffect, useMemo, useState } from 'react'
import { normalizeEmail } from '../utils/format.js'

const STORAGE_KEY = 'event-enrollment.registrations'

// Read saved registrations, falling back to an empty list if storage is
// missing, unavailable or holds malformed data.
function loadRegistrations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function createId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export function useRegistrations() {
  const [registrations, setRegistrations] = useState(loadRegistrations)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(registrations))
    } catch {
      // Storage may be full or blocked; the in-memory state still works.
    }
  }, [registrations])

  // Seats taken per event, derived from the active registrations.
  const bookedCounts = useMemo(() => {
    const counts = {}
    for (const r of registrations) {
      counts[r.eventId] = (counts[r.eventId] ?? 0) + 1
    }
    return counts
  }, [registrations])

  function isEmailRegistered(eventId, email) {
    const target = normalizeEmail(email)
    return registrations.some(
      (r) => r.eventId === eventId && normalizeEmail(r.email) === target,
    )
  }

  function addRegistration(eventId, name, email) {
    const registration = {
      id: createId(),
      eventId,
      name: name.trim(),
      email: email.trim(),
      createdAt: new Date().toISOString(),
    }
    setRegistrations((prev) => [...prev, registration])
    return registration
  }

  function cancelRegistration(id) {
    setRegistrations((prev) => prev.filter((r) => r.id !== id))
  }

  return {
    registrations,
    bookedCounts,
    isEmailRegistered,
    addRegistration,
    cancelRegistration,
  }
}
