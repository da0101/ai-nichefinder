import { renderHook, waitFor, act } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useProfiles } from './useProfiles'

import type { ProfilesResponse } from '@/types/api'

function jsonResponse(payload: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(payload), {
    headers: { 'Content-Type': 'application/json' },
    status: 200,
    ...init,
  })
}

const baseProfiles: ProfilesResponse = {
  active_profile: 'default',
  profiles: [
    {
      slug: 'default',
      site_name: 'Default',
      site_url: 'https://example.com',
      site_description: 'Default profile',
      is_default: true,
      site_config: {
        site_url: 'https://example.com',
        site_name: 'Default',
        site_description: 'Default profile',
        target_audience: 'Founders',
        services: ['web'],
        primary_language: 'en',
        blog_url: 'https://example.com/blog',
        existing_articles: [],
        seed_keywords: [],
        target_persona: 'Founder',
        competitors: [],
        geographic_focus: ['Montreal'],
      },
      database_url: 'sqlite:///data/db/seo.db',
      keywords: 1,
      articles: 0,
      runs: 0,
      approved_noise: 0,
      approved_validity: 0,
      approved_legitimacy: 0,
    },
  ],
}

describe('useProfiles', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads profiles and switches the active profile', async () => {
    const switched: ProfilesResponse = { ...baseProfiles, active_profile: 'consulting' }
    fetchMock
      .mockResolvedValueOnce(jsonResponse(baseProfiles))
      .mockResolvedValueOnce(jsonResponse(switched))

    const { result } = renderHook(() => useProfiles())

    await waitFor(() => {
      expect(result.current.data).toEqual(baseProfiles)
    })

    await act(async () => {
      await result.current.switchProfile('consulting')
    })

    await waitFor(() => {
      expect(result.current.data?.active_profile).toBe('consulting')
    })
  })

  it('falls back to the legacy delete endpoint when DELETE is unsupported', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(baseProfiles))
      .mockResolvedValueOnce(jsonResponse({ error: 'not allowed' }, { status: 405 }))
      .mockResolvedValueOnce(jsonResponse({}))
      .mockResolvedValueOnce(jsonResponse(baseProfiles))

    const { result } = renderHook(() => useProfiles())

    await waitFor(() => {
      expect(result.current.data).toEqual(baseProfiles)
    })

    await act(async () => {
      await result.current.deleteProfile('default')
    })

    expect(fetchMock.mock.calls[1]?.[0]).toBe('/api/profiles/default')
    expect(fetchMock.mock.calls[2]?.[0]).toBe('/api/profiles/delete')
  })
})
