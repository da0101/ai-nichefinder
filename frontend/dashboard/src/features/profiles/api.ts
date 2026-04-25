import type {
  CreateProfileRequest,
  ProfileConfigResponse,
  ProfilesResponse,
  SaveProfileConfigRequest,
  SiteConfigDto,
} from '@/types/api'
import { ApiError, deleteJson, getJson, postJson } from '@/shared/api/http'

export interface CreateProfileInput {
  slug: string
  siteConfig: SiteConfigDto
  use?: boolean
}

export function fetchProfiles(): Promise<ProfilesResponse> {
  return getJson<ProfilesResponse>('/api/profiles')
}

export function switchActiveProfile(profile: string): Promise<ProfilesResponse> {
  return postJson<ProfilesResponse>('/api/profiles/active', { profile })
}

export function createProfile(input: CreateProfileInput): Promise<ProfilesResponse> {
  const payload: CreateProfileRequest = {
    slug: input.slug,
    site_config: input.siteConfig,
    use: input.use,
  }
  return postJson<ProfilesResponse>('/api/profiles', payload)
}

export function saveProfileConfig(profile: string | null, siteConfig: SiteConfigDto): Promise<ProfileConfigResponse> {
  const payload: SaveProfileConfigRequest = {
    profile,
    site_config: siteConfig,
  }
  return postJson<ProfileConfigResponse>('/api/profile-config', payload)
}

export function fetchProfileConfig(profile: string): Promise<ProfileConfigResponse> {
  return getJson<ProfileConfigResponse>(`/api/profile-config?profile=${encodeURIComponent(profile)}`)
}

export async function deleteProfile(profile: string): Promise<ProfilesResponse | Record<string, never>> {
  try {
    return await deleteJson<ProfilesResponse | Record<string, never>>(`/api/profiles/${encodeURIComponent(profile)}`)
  } catch (error) {
    if (error instanceof ApiError && (error.status === 405 || error.status === 501)) {
      return postJson<ProfilesResponse | Record<string, never>>('/api/profiles/delete', { profile })
    }
    throw error
  }
}
