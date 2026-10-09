// "2026-10-08T14:00:00Z" -> "12 min ago". `now` is a parameter so tests can fix it.
export function timeAgo(isoTime, now = new Date()) {
  const minutes = Math.floor((now - new Date(isoTime)) / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.floor(hours / 24)
  return `${days} ${days === 1 ? 'day' : 'days'} ago`
}
