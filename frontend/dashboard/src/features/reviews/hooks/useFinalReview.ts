import { useCallback, useEffect, useState } from 'react'

import type { FinalReviewResponse } from '@/types/api'
import { toErrorMessage } from '@/shared/api/http'

import { fetchFinalReview } from '../api'

interface UseFinalReviewResult {
  data: FinalReviewResponse | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useFinalReview(profiles: string[], intervalMs = 30_000): UseFinalReviewResult {
  const [data, setData] = useState<FinalReviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (profiles.length === 0) {
      setData(null)
      setLoading(false)
      return
    }
    try {
      const json = await fetchFinalReview(profiles)
      setData(json)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [profiles])

  useEffect(() => {
    setLoading(true)
    void refresh()
    if (profiles.length === 0) return
    const timer = setInterval(() => void refresh(), intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs, profiles, refresh])

  return { data, loading, error, refresh }
}
