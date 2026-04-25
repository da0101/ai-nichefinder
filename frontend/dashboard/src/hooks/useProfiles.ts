import { useCallback, useEffect, useState } from 'react'
import type { ProfilesResponse, SiteConfigDto } from '@/types/api'

interface UseProfilesResult {
  data: ProfilesResponse | null
  loading: boolean
  error: string | null
  refreshing: boolean
  clearError: () => void
  refresh: () => Promise<void>
  switchProfile: (profile: string) => Promise<void>
  createProfile: (input: { slug: string; siteConfig: SiteConfigDto; use?: boolean }) => Promise<void>
  updateProfile: (profile: string, siteConfig: SiteConfigDto) => Promise<void>
  deleteProfile: (profile: string) => Promise<void>
}

export function useProfiles(): UseProfilesResult {
  const [data, setData] = useState<ProfilesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const refresh = useCallback(async () => {
    setRefreshing(true)
    try {
      const response = await fetch('/api/profiles')
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      const json: ProfilesResponse = await response.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  const switchProfile = useCallback(async (profile: string) => {
    setRefreshing(true)
    setError(null)
    try {
      const response = await fetch('/api/profiles/active', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      const json: ProfilesResponse = await response.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      throw e
    } finally {
      setRefreshing(false)
      setLoading(false)
    }
  }, [])

  const createProfile = useCallback(async ({ slug, siteConfig, use = false }: { slug: string; siteConfig: SiteConfigDto; use?: boolean }) => {
    setRefreshing(true)
    setError(null)
    try {
      const response = await fetch('/api/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slug, site_config: siteConfig, use }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      throw e
    } finally {
      setRefreshing(false)
    }
  }, [refresh])

  const updateProfile = useCallback(async (profile: string, siteConfig: SiteConfigDto) => {
    setRefreshing(true)
    setError(null)
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
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      throw e
    } finally {
      setRefreshing(false)
    }
  }, [refresh])

  const deleteProfile = useCallback(async (profile: string) => {
    setRefreshing(true)
    setError(null)
    try {
      let response = await fetch(`/api/profiles/${encodeURIComponent(profile)}`, {
        method: 'DELETE',
      })
      if (response.status === 501 || response.status === 405) {
        response = await fetch('/api/profiles/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ profile }),
        })
      }
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      throw e
    } finally {
      setRefreshing(false)
    }
  }, [refresh])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { data, loading, error, refreshing, clearError, refresh, switchProfile, createProfile, updateProfile, deleteProfile }
}
