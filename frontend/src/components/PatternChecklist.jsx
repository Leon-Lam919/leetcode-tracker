import DifficultyBadge from './DifficultyBadge'

function ProgressBar({ done, total, label }) {
  const percent = total === 0 ? 0 : Math.round((done / total) * 100)
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={done}
      aria-valuemin={0}
      aria-valuemax={total}
      className="h-2 w-full overflow-hidden rounded bg-gray-200 dark:bg-gray-700"
    >
      <div className="h-full bg-green-500" style={{ width: `${percent}%` }} />
    </div>
  )
}

function ProblemRow({ problem }) {
  return (
    <li className="flex flex-wrap items-center gap-2 py-1 text-sm">
      <span aria-label={problem.solved ? 'solved' : 'not solved'}>
        {problem.solved ? '✅' : '⬜'}
      </span>
      <a
        href={problem.url}
        target="_blank"
        rel="noreferrer"
        className={
          problem.solved
            ? 'text-gray-600 dark:text-gray-300'
            : 'font-medium text-blue-700 hover:underline dark:text-blue-400'
        }
      >
        {problem.title}
      </a>
      <DifficultyBadge difficulty={problem.difficulty} />
      {problem.needs_review && <span title="Needs review">🔁</span>}
    </li>
  )
}

// `groups` comes from /api/patterns: one entry per pattern, in NeetCode order.
export default function PatternChecklist({ groups }) {
  const solved = groups.reduce((sum, group) => sum + group.solved, 0)
  const total = groups.reduce((sum, group) => sum + group.total, 0)

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <p className="text-sm text-gray-500 dark:text-gray-400">NeetCode 150 progress</p>
        <p className="text-3xl font-bold">
          {solved} / {total}
        </p>
        <ProgressBar done={solved} total={total} label="Overall progress" />
      </div>

      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {groups.map((group) => (
          <details key={group.pattern} className="py-2">
            <summary className="cursor-pointer list-none space-y-1">
              <span className="flex justify-between text-sm font-medium">
                <span>{`${group.pattern} ${group.solved}/${group.total}`}</span>
                <span className="text-gray-400">▾</span>
              </span>
              <ProgressBar done={group.solved} total={group.total} label={group.pattern} />
            </summary>
            <ul className="mt-2">
              {group.problems.map((problem) => (
                <ProblemRow key={problem.slug} problem={problem} />
              ))}
            </ul>
          </details>
        ))}
      </div>
    </div>
  )
}
