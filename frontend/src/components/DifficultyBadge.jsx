const COLORS = {
  Easy: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300',
  Medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300',
  Hard: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
}

export default function DifficultyBadge({ difficulty }) {
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${COLORS[difficulty] ?? ''}`}>
      {difficulty}
    </span>
  )
}
