import { useEffect, useState } from 'react'

import type { KeywordDetailResponse } from '@/types/api'
import { toErrorMessage } from '@/shared/api/http'

import { fetchKeywordDetail } from '../api'

interface UseKeywordDetailResult {
  data: KeywordDetailResponse | null
  loading: boolean
  error: string | null
}

export function useKeywordDetail(id: string | null, intervalMs = 30_000): UseKeywordDetailResult {
  const [data, setData] = useState<KeywordDetailResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) {
      setData(null)
      setLoading(false)
      return
    }

    const controller = new AbortController()
    let timer: ReturnType<typeof setInterval> | null = null

    const load = (showLoading: boolean) => {
      if (showLoading) setLoading(true)
      setError(null)
      fetchKeywordDetail(id, controller.signal)
        .then(json => {
          setData(json)
          setLoading(false)
        })
        .catch(error => {
          if (error instanceof Error && error.name === 'AbortError') {
            return
          }
          setError(toErrorMessage(error))
          setLoading(false)
        })
    }

    load(true)
    timer = setInterval(() => load(false), intervalMs)
    return () => {
      controller.abort()
      if (timer) clearInterval(timer)
    }
  }, [id, intervalMs])

  return { data, loading, error }
}
