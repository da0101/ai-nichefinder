import { useCallback, useEffect, useState } from 'react'

import type { ProfilesResponse, SiteConfigDto } from '@/types/api'
import { toErrorMessage } from '@/shared/api/http'

import {
  createProfile as createProfileRequest,
  deleteProfile as deleteProfileRequest,
  fetchProfiles,
  switchActiveProfile,
  type CreateProfileInput,
  saveProfileConfig as saveProfileConfigRequest,
} from '../api'

interface UseProfilesResult {
  data: ProfilesResponse | null
  loading: boolean
  error: string | null
  refreshing: boolean
  clearError: () => void
  refresh: () => Promise<void>
  switchProfile: (profile: string) => Promise<void>
  createProfile: (input: CreateProfileInput) => Promise<void>
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
      const json = await fetchProfiles()
      setData(json)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error))
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  const switchProfile = useCallback(async (profile: string) => {
    setRefreshing(true)
    setError(null)
    try {
      const json = await switchActiveProfile(profile)
      setData(json)
    } catch (error) {
      setError(toErrorMessage(error))
      throw error
    } finally {
      setRefreshing(false)
      setLoading(false)
    }
  }, [])

  const createProfile = useCallback(async (input: CreateProfileInput) => {
    setRefreshing(true)
    setError(null)
    try {
      await createProfileRequest(input)
      await refresh()
    } catch (error) {
      setError(toErrorMessage(error))
      throw error
    } finally {
      setRefreshing(false)
    }
  }, [refresh])

  const updateProfile = useCallback(async (profile: string, siteConfig: SiteConfigDto) => {
    setRefreshing(true)
    setError(null)
    try {
      await saveProfileConfigRequest(profile, siteConfig)
      await refresh()
    } catch (error) {
      setError(toErrorMessage(error))
      throw error
    } finally {
      setRefreshing(false)
    }
  }, [refresh])

  const deleteProfile = useCallback(async (profile: string) => {
    setRefreshing(true)
    setError(null)
    try {
      await deleteProfileRequest(profile)
      await refresh()
    } catch (error) {
      setError(toErrorMessage(error))
      throw error
    } finally {
      setRefreshing(false)
    }
  }, [refresh])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { data, loading, error, refreshing, clearError, refresh, switchProfile, createProfile, updateProfile, deleteProfile }
}
