import { useCallback, useEffect, useState } from 'react'
import type { ProfileConfigResponse } from '@/types/api'

interface UseProfileConfigResult {
  data: ProfileConfigResponse | null
  loading: boolean
  error: string | null
  saving: boolean
  refresh: () => Promise<void>
  save: (siteConfig: ProfileConfigResponse['site_config']) => Promise<void>
}

export function useProfileConfig(profile: string | null): UseProfileConfigResult {
  const [data, setData] = useState<ProfileConfigResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!profile) {
      setData(null)
      setLoading(false)
      return
    }
    try {
      const response = await fetch(`/api/profile-config?profile=${encodeURIComponent(profile)}`)
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      const json: ProfileConfigResponse = await response.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [profile])

  const save = useCallback(async (siteConfig: ProfileConfigResponse['site_config']) => {
    setSaving(true)
    try {
      const response = await fetch('/api/profile-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile, site_config: siteConfig }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      const json: ProfileConfigResponse = await response.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      throw e
    } finally {
      setSaving(false)
    }
  }, [profile])

  useEffect(() => {
    setLoading(true)
    void refresh()
  }, [refresh])

  return { data, loading, error, saving, refresh, save }
}
