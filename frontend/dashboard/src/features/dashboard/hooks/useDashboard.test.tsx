import { renderHook, waitFor, act } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useDashboard } from './useDashboard'

import type { DashboardResponse } from '@/types/api'

function jsonResponse(payload: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(payload), {
    headers: { 'Content-Type': 'application/json' },
    status: 200,
    ...init,
  })
}

describe('useDashboard', () => {
  const fetchMock = vi.fn<typeof fetch>()
  const first: DashboardResponse = {
    summary: { total_keywords: 1, briefed_keywords: 0, articles: 0, published_articles: 0 },
    keywords: [],
    articles: [],
    usage: [],
    paths: { database: 'sqlite:///test.db', articles_dir: '/tmp/articles' },
  }
  const second: DashboardResponse = {
    ...first,
    summary: { ...first.summary, total_keywords: 2 },
  }

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads dashboard data and supports manual refresh', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(first))
      .mockResolvedValueOnce(jsonResponse(second))

    const { result } = renderHook(() => useDashboard(60_000))

    await waitFor(() => {
      expect(result.current.data).toEqual(first)
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.refresh()
    })

    await waitFor(() => {
      expect(result.current.data).toEqual(second)
    })
  })
})
