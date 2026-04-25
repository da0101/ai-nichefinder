import { useCallback, useEffect, useState } from 'react'
import type { TrainingReviewResponse } from '@/types/api'

interface TrainingApprovalPayload {
  profile: string
  noise_keyword_phrases?: string[]
  noise_secondary_phrases?: string[]
  noise_domains?: string[]
  valid_keyword_phrases?: string[]
  valid_secondary_phrases?: string[]
  trusted_domains?: string[]
}

interface UseTrainingReviewResult {
  data: TrainingReviewResponse | null
  loading: boolean
  error: string | null
  approving: boolean
  refresh: () => Promise<void>
  approve: (payload: TrainingApprovalPayload) => Promise<void>
}

export function useTrainingReview(profile: string | null, intervalMs = 30_000): UseTrainingReviewResult {
  const [data, setData] = useState<TrainingReviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!profile) {
      setData(null)
      setLoading(false)
      return
    }
    try {
      const response = await fetch(`/api/training-review?profile=${encodeURIComponent(profile)}`)
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      const json: TrainingReviewResponse = await response.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [profile])

  const approve = useCallback(async (payload: TrainingApprovalPayload) => {
    setApproving(true)
    try {
      const response = await fetch('/api/training-approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      const json: TrainingReviewResponse = await response.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      throw e
    } finally {
      setApproving(false)
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    void refresh()
    if (!profile) return
    const timer = setInterval(() => void refresh(), intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs, profile, refresh])

  return { data, loading, error, approving, refresh, approve }
}
