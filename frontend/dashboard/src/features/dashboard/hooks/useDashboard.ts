import { useCallback, useEffect, useRef, useState } from 'react'

import type { DashboardResponse } from '@/types/api'
import { toErrorMessage } from '@/shared/api/http'

import { fetchDashboard } from '../api'

interface UseDashboardResult {
  data: DashboardResponse | null
  loading: boolean
  error: string | null
  lastUpdated: Date | null
  refresh: () => Promise<void>
}

export function useDashboard(intervalMs = 30_000): UseDashboardResult {
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const refresh = useCallback(async () => {
    try {
      const json = await fetchDashboard()
      setData(json)
      setError(null)
      setLastUpdated(new Date())
    } catch (error) {
      setError(toErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    timerRef.current = setInterval(() => void refresh(), intervalMs)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [intervalMs, refresh])

  return { data, loading, error, lastUpdated, refresh }
}
