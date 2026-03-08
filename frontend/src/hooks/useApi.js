import { useState, useEffect, useCallback } from 'react'

export function useApi(fetcher, deps = [], interval = null) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    try {
      const result = await fetcher()
      setData(result)
      setError(null)
    } catch (e) {
      setError(e.message || 'Error')
    } finally {
      setLoading(false)
    }
  }, deps)

  useEffect(() => {
    fetch()
    if (interval) {
      const timer = setInterval(fetch, interval)
      return () => clearInterval(timer)
    }
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}
