import { useState } from 'react'
import { addSolve } from '../api'
import { extractSlug } from '../slug'
import RatingButtons from './RatingButtons'

const inputClass =
  'w-full rounded border border-gray-300 bg-white p-2 dark:border-gray-600 dark:bg-gray-800'

export default function AddSolveForm({ onAdded }) {
  const [input, setInput] = useState('')
  const [solvedDate, setSolvedDate] = useState('') // empty = today (the backend decides)
  // Shown only if the LeetCode lookup fails, so the problem can be entered by hand.
  const [showDetails, setShowDetails] = useState(false)
  const [title, setTitle] = useState('')
  const [difficulty, setDifficulty] = useState('Easy')
  // Optional rating, picked before pressing Add. null = not rated (Enter still submits).
  const [confidence, setConfidence] = useState(null)
  const [needsReview, setNeedsReview] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    const slug = extractSlug(input)
    if (!slug) return

    const body = { title_slug: slug }
    if (solvedDate) body.solved_date = solvedDate
    if (showDetails) Object.assign(body, { title, difficulty })
    if (confidence !== null) Object.assign(body, { confidence, needs_review: needsReview })
    else if (needsReview) body.needs_review = true

    setSaving(true)
    setError('')
    try {
      await addSolve(body)
      setInput('')
      setShowDetails(false)
      setTitle('')
      setConfidence(null)
      setNeedsReview(false)
      onAdded()
    } catch (err) {
      setError(err.message)
      if (err.status === 502) setShowDetails(true) // lookup failed: let the user fill it in
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <label className="block text-sm font-medium" htmlFor="add-solve-input">
        Add a solve by slug or URL
      </label>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          id="add-solve-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="https://leetcode.com/problems/two-sum/"
          className={inputClass}
        />
        <input
          type="date"
          aria-label="Solved date"
          value={solvedDate}
          onChange={(event) => setSolvedDate(event.target.value)}
          className={`${inputClass} sm:w-44`}
        />
        <button
          type="submit"
          disabled={saving || !input.trim()}
          className="rounded-lg bg-gray-800 px-4 py-2 font-semibold text-white hover:bg-gray-700 disabled:opacity-50 dark:bg-gray-200 dark:text-gray-900"
        >
          {saving ? 'Adding…' : 'Add'}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-gray-500 dark:text-gray-400">Rating (optional):</span>
        <RatingButtons
          selected={confidence}
          onRate={(value) => setConfidence((current) => (current === value ? null : value))}
        />
        <label className="flex items-center gap-1">
          <input
            type="checkbox"
            checked={needsReview}
            onChange={(event) => setNeedsReview(event.target.checked)}
          />
          🔁 flag for review
        </label>
      </div>

      {showDetails && (
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Title, e.g. Two Sum"
            aria-label="Title"
            className={inputClass}
          />
          <select
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
            aria-label="Difficulty"
            className={`${inputClass} sm:w-36`}
          >
            <option>Easy</option>
            <option>Medium</option>
            <option>Hard</option>
          </select>
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-400">
          {error}
        </p>
      )}
    </form>
  )
}
