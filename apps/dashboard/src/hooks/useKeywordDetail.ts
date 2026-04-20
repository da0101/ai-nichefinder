import { useEffect, useState } from 'react'
import type { KeywordDetailResponse } from '@/types/api'

interface UseKeywordDetailResult {
  data: KeywordDetailResponse | null
  loading: boolean
  error: string | null
}

export function useKeywordDetail(id: string | null): UseKeywordDetailResult {
  const [data, setData] = useState<KeywordDetailResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) {
      setData(null)
      return
    }
    setLoading(true)
    setError(null)
    const controller = new AbortController()
    fetch(`/api/keywords/${id}`, { signal: controller.signal })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((json: KeywordDetailResponse) => {
        setData(json)
        setLoading(false)
      })
      .catch(e => {
        if (e.name !== 'AbortError') {
          setError(e instanceof Error ? e.message : 'Error')
          setLoading(false)
        }
      })
    return () => controller.abort()
  }, [id])

  return { data, loading, error }
}
