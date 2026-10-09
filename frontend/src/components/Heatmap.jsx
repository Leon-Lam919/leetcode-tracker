// A GitHub-style grid built with plain CSS grid: 7 rows (Sun..Sat), one column per week.
// `days` comes from /api/heatmap: [{ date: "2026-10-08", count: 1 }, ...], oldest first.

function cellColor(count) {
  if (count === 0) return 'bg-gray-200 dark:bg-gray-700'
  if (count === 1) return 'bg-green-300 dark:bg-green-800'
  if (count === 2) return 'bg-green-500 dark:bg-green-600'
  return 'bg-green-700 dark:bg-green-400'
}

// "2026-10-08" -> 0 (Sunday) .. 6 (Saturday). Parsed as UTC so the browser's
// timezone can't shift it to the previous day.
function weekday(isoDate) {
  return new Date(`${isoDate}T00:00:00Z`).getUTCDay()
}

export default function Heatmap({ days }) {
  if (days.length === 0) return null

  // Empty cells before the first day, so each date lands in its weekday's row.
  const padding = weekday(days[0].date)
  const today = days[days.length - 1].date // the backend's "today" is always the last entry

  return (
    <div className="overflow-x-auto">
      <div className="grid w-max grid-flow-col grid-rows-7 gap-[3px]">
        {Array.from({ length: padding }, (_, i) => (
          <div key={`pad-${i}`} className="h-3 w-3" />
        ))}
        {days.map((day) => {
          const isToday = day.date === today
          return (
            <div
              key={day.date}
              data-testid="heatmap-cell"
              data-today={isToday || undefined}
              title={`${day.date}: ${day.count} ${day.count === 1 ? 'solve' : 'solves'}`}
              className={`h-3 w-3 rounded-sm ${cellColor(day.count)} ${
                isToday ? 'ring-2 ring-blue-500 ring-offset-1 dark:ring-offset-gray-900' : ''
              }`}
            />
          )
        })}
      </div>
    </div>
  )
}
