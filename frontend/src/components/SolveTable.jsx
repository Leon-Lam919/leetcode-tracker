import DifficultyBadge from './DifficultyBadge'

const CONFIDENCE_LABELS = { 1: 'Needed help', 2: 'Okay', 3: 'Clean' }

export default function SolveTable({ solves, onSelect }) {
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
              <td className="hidden py-2 pr-3 sm:table-cell">
                {CONFIDENCE_LABELS[solve.confidence] ?? '—'}
              </td>
              <td className="py-2">{solve.needs_review ? '🔁' : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
