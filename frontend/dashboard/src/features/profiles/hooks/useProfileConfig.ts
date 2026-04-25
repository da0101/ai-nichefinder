import { useCallback, useEffect, useState } from 'react'

import type { ProfileConfigResponse } from '@/types/api'
import { toErrorMessage } from '@/shared/api/http'

import { fetchProfileConfig, saveProfileConfig } from '../api'

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
      const json = await fetchProfileConfig(profile)
      setData(json)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [profile])

  const save = useCallback(async (siteConfig: ProfileConfigResponse['site_config']) => {
    setSaving(true)
    try {
      const json = await saveProfileConfig(profile, siteConfig)
      setData(json)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error))
      throw error
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
