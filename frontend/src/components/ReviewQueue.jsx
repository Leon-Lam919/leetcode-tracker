import { useState } from 'react'
import { markReviewed } from '../api'
import DifficultyBadge from './DifficultyBadge'

const BUTTONS = [
  { label: 'Again', confidence: 1, className: 'bg-red-600 hover:bg-red-700' },
  { label: 'Good', confidence: 2, className: 'bg-blue-600 hover:bg-blue-700' },
  { label: 'Easy', confidence: 3, className: 'bg-green-600 hover:bg-green-700' },
]

function overdueText(days) {
  if (days === 0) return 'due today'
  return `${days} ${days === 1 ? 'day' : 'days'} overdue`
}

// `reviews` comes from /api/reviews/due. After a button press, onReviewed() refetches.
export default function ReviewQueue({ reviews, onReviewed }) {
  const [busyId, setBusyId] = useState(null) // problem being saved
  const [error, setError] = useState('')

  async function handleReview(problemId, confidence) {
    setBusyId(problemId)
    setError('')
    try {
      await markReviewed(problemId, confidence)
      onReviewed()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  if (reviews.length === 0) {
    return <p className="text-gray-500 dark:text-gray-400">Nothing to review today 🎉</p>
  }

  return (
    <div className="space-y-3">
      <h2 className="font-semibold">🔁 {reviews.length} to review today</h2>
      <ul className="space-y-2">
        {reviews.map((review) => (
          <li
            key={review.problem_id}
            className="flex flex-col gap-2 border-t border-gray-200 pt-2 sm:flex-row sm:items-center sm:justify-between dark:border-gray-700"
          >
            <div>
              <a
                href={review.url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-blue-700 hover:underline dark:text-blue-400"
              >
                {review.title}
              </a>{' '}
              <DifficultyBadge difficulty={review.difficulty} />
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {overdueText(review.days_overdue)}
                {review.approach && ` · ${review.approach}`}
              </p>
            </div>
            <div className="flex gap-2">
              {BUTTONS.map(({ label, confidence, className }) => (
                <button
                  key={label}
                  type="button"
                  disabled={busyId === review.problem_id}
                  onClick={() => handleReview(review.problem_id, confidence)}
                  aria-label={`${label}: ${review.title}`}
                  className={`rounded px-3 py-1 text-sm font-semibold text-white disabled:opacity-50 ${className}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </li>
        ))}
      </ul>
      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}
