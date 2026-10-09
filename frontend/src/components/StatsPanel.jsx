const DIFFICULTY_STYLES = [
  ['Easy', 'text-green-600 dark:text-green-400'],
  ['Medium', 'text-yellow-600 dark:text-yellow-400'],
  ['Hard', 'text-red-600 dark:text-red-400'],
]

export default function StatsPanel({ stats }) {
  // by_topic arrives sorted biggest first, so the first 5 are the top 5.
  const topTopics = Object.entries(stats.by_topic).slice(0, 5)

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">Problems solved</p>
        <p className="text-3xl font-bold">{stats.total_solved}</p>
        <div className="mt-2 flex gap-4">
          {DIFFICULTY_STYLES.map(([difficulty, color]) => (
            <span key={difficulty} className={`font-semibold ${color}`}>
              {difficulty} {stats.by_difficulty[difficulty] ?? 0}
            </span>
          ))}
        </div>
      </div>

      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">Top topics</p>
        {topTopics.length === 0 ? (
          <p className="text-sm">None yet</p>
        ) : (
          <ul className="mt-1 space-y-1 text-sm">
            {topTopics.map(([topic, count]) => (
              <li key={topic} className="flex justify-between">
                <span>{topic}</span>
                <span className="font-semibold">{count}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
