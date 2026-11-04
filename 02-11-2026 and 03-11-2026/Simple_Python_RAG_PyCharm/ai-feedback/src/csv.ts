/** Minimal CSV export: proper quoting, UTF-8 BOM so Excel shows non-ASCII text correctly. */

export interface CsvColumn<T> {
  header: string
  value: (row: T) => string | number | null | undefined
}

function cell(v: string | number | null | undefined): string {
  const s = v == null ? '' : String(v)
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export function toCsv<T>(rows: T[], columns: CsvColumn<T>[]): string {
  const lines = [columns.map((c) => cell(c.header)).join(',')]
  for (const r of rows) lines.push(columns.map((c) => cell(c.value(r))).join(','))
  return lines.join('\r\n')
}

export function downloadCsv<T>(filename: string, rows: T[], columns: CsvColumn<T>[]) {
  const blob = new Blob(['﻿' + toCsv(rows, columns)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

/** e.g. "2026-11-02_15-40-12", for unique export file names. */
export const fileStamp = () => new Date().toISOString().slice(0, 19).replace('T', '_').replace(/:/g, '-')
