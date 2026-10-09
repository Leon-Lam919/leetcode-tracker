// Shows "Loading…" or an error while `data` isn't ready, otherwise renders children.
export default function Status({ loading, error, data, children }) {
  if (error) {
    return (
      <p role="alert" className="text-sm text-red-700 dark:text-red-400">
        Couldn't load: {error}
      </p>
    )
  }
  if (data === null) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">{loading ? 'Loading…' : ''}</p>
  }
  return children
}
