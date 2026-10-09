export default function TodayBanner({ stats }) {
  const done = stats.today_done

  return (
    <section
      className={`rounded-xl p-4 ${
        done
          ? 'bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-100'
          : 'bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100'
      }`}
    >
      <p className="text-3xl font-bold">{done ? '✅ Done today' : '❌ Not yet today'}</p>
      <p className="mt-1 text-sm">
        {stats.today_count} / {stats.daily_goal} solved today
      </p>
      <div className="mt-3 flex gap-6 text-lg">
        <span>
          🔥 <strong>{stats.current_streak}</strong> day streak
        </span>
        <span>
          Best: <strong>{stats.longest_streak}</strong>
        </span>
      </div>
    </section>
  )
}
