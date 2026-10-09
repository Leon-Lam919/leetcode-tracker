import { useState } from 'react'
import { deleteSolve, updateSolve } from '../api'

const inputClass =
  'w-full rounded border border-gray-300 bg-white p-2 dark:border-gray-600 dark:bg-gray-800'

export default function NoteEditor({ solve, onSaved, onClose }) {
  // Form fields are strings while editing; they're converted when saving.
  const [timeSpent, setTimeSpent] = useState(solve.time_spent_min?.toString() ?? '')
  const [confidence, setConfidence] = useState(solve.confidence?.toString() ?? '')
  const [notes, setNotes] = useState(solve.notes)
  const [needsReview, setNeedsReview] = useState(solve.needs_review)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function run(action) {
    setSaving(true)
    setError('')
    try {
      await action()
      onSaved()
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  function handleSave(event) {
    event.preventDefault()
    run(() =>
      updateSolve(solve.id, {
        time_spent_min: timeSpent === '' ? null : Number(timeSpent),
        confidence: confidence === '' ? null : Number(confidence),
        notes,
        needs_review: needsReview,
      }),
    )
  }

  function handleDelete() {
    if (window.confirm(`Delete this solve of "${solve.title}"?`)) {
      run(() => deleteSolve(solve.id))
    }
  }

  return (
    <form
      onSubmit={handleSave}
      className="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-gray-700"
    >
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-semibold">
          {solve.title} <span className="font-normal text-gray-500">· {solve.solved_date}</span>
        </h2>
        <button type="button" onClick={onClose} aria-label="Close" className="px-2 text-xl">
          ×
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <label className="text-sm">
          Time (min)
          <input
            type="number"
            min="0"
            value={timeSpent}
            onChange={(event) => setTimeSpent(event.target.value)}
            className={inputClass}
          />
        </label>
        <label className="text-sm">
          Confidence
          <select
            value={confidence}
            onChange={(event) => setConfidence(event.target.value)}
            className={inputClass}
          >
            <option value="">—</option>
            <option value="1">1 · needed help</option>
            <option value="2">2 · okay</option>
            <option value="3">3 · clean</option>
          </select>
        </label>
      </div>

      <label className="block text-sm">
        Notes
        <textarea
          rows={4}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          className={inputClass}
        />
      </label>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={needsReview}
          onChange={(event) => setNeedsReview(event.target.checked)}
        />
        Needs review
      </label>

      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-400">
          {error}
        </p>
      )}

      <div className="flex justify-between">
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          onClick={handleDelete}
          disabled={saving}
          className="text-sm text-red-700 hover:underline dark:text-red-400"
        >
          Delete solve
        </button>
      </div>
    </form>
  )
}
