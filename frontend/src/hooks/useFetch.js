import { useEffect, useState } from 'react'

// Calls fetcher(arg) on mount and again whenever `version` or `arg` changes.
// Returns { data, loading, error }. Old data stays visible while a refetch runs,
// so the screen never goes blank.
export function useFetch(fetcher, version, arg) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false // set if the component re-renders before this request finishes
    setLoading(true)
    setError('')
    fetcher(arg)
      .then((result) => {
        if (!ignore) setData(result)
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [fetcher, version, arg])

  return { data, loading, error }
}
