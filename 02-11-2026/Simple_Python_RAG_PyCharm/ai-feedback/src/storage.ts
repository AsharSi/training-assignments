import { useEffect, useState } from 'react'

const PREFIX = 'aiFeedback.'

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

interface Options<T> {
  /** Wins over the stored value on first render. */
  override?: T
  /** Applied to the stored value on load (e.g. sorting); the result is saved back. */
  normalize?: (value: T) => T
}

/** useState that persists to localStorage under "aiFeedback.<key>". */
export function useLocalStorage<T>(key: string, fallback: T, { override, normalize }: Options<T> = {}) {
  const [value, setValue] = useState<T>(() => {
    const loaded = override ?? load(key, fallback)
    return normalize ? normalize(loaded) : loaded
  })
  useEffect(() => {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(value))
    } catch {
      /* storage full or blocked: keep working in memory */
    }
  }, [key, value])
  return [value, setValue] as const
}

export const newId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
