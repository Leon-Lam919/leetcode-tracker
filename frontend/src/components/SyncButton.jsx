import { useState } from 'react'
import { syncNow } from '../api'
import { timeAgo } from '../timeAgo'

// lastSyncAt / lastSyncResult come from /api/stats (set by manual and scheduled syncs).
export default function SyncButton({ onSynced, lastSyncAt, lastSyncResult }) {
  const [running, setRunning] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function handleClick() {
    setRunning(true)
    setMessage('')
    setError('')
    try {
      const result = await syncNow()
      setMessage(`Added ${result.added}`)
      onSynced()
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={handleClick}
        disabled={running}
        className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {running ? 'Syncing…' : 'Sync now'}
      </button>
      {lastSyncAt && !running && (
        <span title={lastSyncResult ?? ''} className="text-sm text-gray-500 dark:text-gray-400">
          Synced {timeAgo(lastSyncAt)}
          {lastSyncResult?.startsWith('failed') && ' (failed)'}
        </span>
      )}
      {message && <span className="text-sm text-green-700 dark:text-green-400">{message}</span>}
      {error && (
        <span role="alert" className="text-sm text-red-700 dark:text-red-400">
          {error}
        </span>
      )}
    </div>
  )
}
