import { useState } from 'react'
import { updateSolve } from '../api'
import DifficultyBadge from './DifficultyBadge'
import RatingButtons from './RatingButtons'

const CONFIDENCE_LABELS = { 1: 'Needed help', 2: 'Okay', 3: 'Clean' }

// Confidence cell for an unrated solve: a "Rate" chip that opens the three buttons in place.
function InlineRate({ solve, onRated }) {
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleRate(confidence) {
    setSaving(true)
    setError('')
    try {
      await updateSolve(solve.id, { confidence })
      onRated()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={`Rate ${solve.title}`}
        className="rounded-full border border-gray-300 px-2 py-0.5 text-xs hover:bg-gray-200 dark:border-gray-600 dark:hover:bg-gray-700"
      >
        Rate
      </button>
    )
  }
  return (
    <div className="space-y-1">
      <RatingButtons name={solve.title} disabled={saving} onRate={handleRate} />
      {error && (
        <p role="alert" className="text-xs text-red-700 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}

export default function SolveTable({ solves, onSelect, onRated = () => {} }) {
  if (solves.length === 0) {
    return <p className="text-gray-500 dark:text-gray-400">No solves yet. Sync or add one.</p>
  }

  return (
    // overflow-x-auto: on a narrow phone the table scrolls instead of breaking the layout.
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-gray-500 dark:text-gray-400">
          <tr>
            <th className="py-2 pr-3">Problem</th>
            <th className="py-2 pr-3">Date</th>
            <th className="hidden py-2 pr-3 sm:table-cell">Topics</th>
            <th className="hidden py-2 pr-3 sm:table-cell">Confidence</th>
            <th className="py-2">Review</th>
          </tr>
        </thead>
        <tbody>
          {solves.map((solve) => (
            <tr
              key={solve.id}
              onClick={() => onSelect(solve)}
              className="cursor-pointer border-t border-gray-200 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
            >
              <td className="py-2 pr-3">
                <a
                  href={solve.url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={(event) => event.stopPropagation()} // open LeetCode, not the editor
                  className="font-medium text-blue-700 hover:underline dark:text-blue-400"
                >
                  {solve.title}
                </a>
                {(solve.approach || solve.code) && (
                  <span title="Has a written solution" className="ml-1">
                    📝
                  </span>
                )}
                <div className="mt-1">
                  <DifficultyBadge difficulty={solve.difficulty} />
                </div>
              </td>
              <td className="whitespace-nowrap py-2 pr-3">{solve.solved_date}</td>
              <td className="hidden py-2 pr-3 sm:table-cell">{solve.topics.join(', ')}</td>
              <td
                className="hidden py-2 pr-3 sm:table-cell"
                // Clicks inside the cell rate in place instead of opening the editor.
                onClick={solve.confidence ? undefined : (event) => event.stopPropagation()}
              >
                {solve.confidence ? (
                  CONFIDENCE_LABELS[solve.confidence]
                ) : (
                  <InlineRate solve={solve} onRated={onRated} />
                )}
              </td>
              <td className="py-2">{solve.needs_review ? '🔁' : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
