import { useCallback, useEffect, useState } from 'react'

import type { TrainingApprovalRequest, TrainingReviewResponse } from '@/types/api'
import { toErrorMessage } from '@/shared/api/http'

import { approveTraining, fetchTrainingReview } from '../api'

interface UseTrainingReviewResult {
  data: TrainingReviewResponse | null
  loading: boolean
  error: string | null
  approving: boolean
  refresh: () => Promise<void>
  approve: (payload: TrainingApprovalRequest) => Promise<void>
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
      const json = await fetchTrainingReview(profile)
      setData(json)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [profile])

  const approve = useCallback(async (payload: TrainingApprovalRequest) => {
    setApproving(true)
    try {
      const json = await approveTraining(payload)
      setData(json)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error))
      throw error
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
