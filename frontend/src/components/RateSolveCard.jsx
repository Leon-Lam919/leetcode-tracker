import { useState } from 'react'
import { updateSolve } from '../api'
import { TIME_CHIPS } from '../ratings'
import DifficultyBadge from './DifficultyBadge'
import RatingButtons from './RatingButtons'

const chipClass = (active) =>
  `rounded-full border px-2 py-0.5 text-xs ${
    active
      ? 'border-gray-800 bg-gray-800 text-white dark:border-gray-200 dark:bg-gray-200 dark:text-gray-900'
      : 'border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300'
  }`

// One unrated solve. A click on Again / Good / Easy saves everything in one PATCH.
function RateRow({ solve, onRated, onSkip }) {
  const [needsReview, setNeedsReview] = useState(solve.needs_review)
  const [minutes, setMinutes] = useState(null) // null = no chip picked
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleRate(confidence) {
    if (saving) return
    const changes = { confidence, needs_review: needsReview }
    if (minutes !== null) changes.time_spent_min = minutes
    setSaving(true)
    setError('')
    try {
      await updateSolve(solve.id, changes)
      onRated(solve.id)
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <li className="space-y-2 border-t border-gray-200 pt-2 dark:border-gray-700">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <a
            href={solve.url}
            target="_blank"
            rel="noreferrer"
            className="font-medium text-blue-700 hover:underline dark:text-blue-400"
          >
            {solve.title}
          </a>{' '}
          <DifficultyBadge difficulty={solve.difficulty} />
        </div>
        <RatingButtons name={solve.title} disabled={saving} onRate={handleRate} />
      </div>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <button
          type="button"
          aria-pressed={needsReview}
          onClick={() => setNeedsReview((on) => !on)}
          className={chipClass(needsReview)}
        >
          🔁 flag for review
        </button>
        <span className="text-xs text-gray-500 dark:text-gray-400">Time:</span>
        {TIME_CHIPS.map(({ label, minutes: value }) => (
          <button
            key={label}
            type="button"
            aria-pressed={minutes === value}
            aria-label={`${label} min`}
            onClick={() => setMinutes((current) => (current === value ? null : value))}
            className={chipClass(minutes === value)}
          >
            {label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => onSkip(solve.id)}
          className="ml-auto text-xs text-gray-500 hover:underline dark:text-gray-400"
        >
          Skip
        </button>
      </div>
      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-400">
          {error}
        </p>
      )}
    </li>
  )
}

// `solves` comes from /api/solves/unrated. Renders nothing when there's nothing to rate.
// Skipped and just-rated rows are hidden right away (skips last until the page reloads).
export default function RateSolveCard({ solves, onRated }) {
  const [hidden, setHidden] = useState(() => new Set())
  const hide = (id) => setHidden((ids) => new Set(ids).add(id))
  const visible = solves.filter((solve) => !hidden.has(solve.id))

  if (visible.length === 0) return null

  return (
    <section className="space-y-3 rounded-xl bg-white p-4 shadow-sm dark:bg-gray-800/60">
      <h2 className="font-semibold">✍️ Rate today&apos;s solves ({visible.length})</h2>
      <ul className="space-y-2">
        {visible.map((solve) => (
          <RateRow
            key={solve.id}
            solve={solve}
            onSkip={hide}
            onRated={(id) => {
              hide(id)
              onRated()
            }}
          />
        ))}
      </ul>
    </section>
  )
}
