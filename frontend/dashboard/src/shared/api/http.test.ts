import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

import { ApiError, deleteJson, getJson, postJson } from './http'

function jsonResponse(payload: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(payload), {
    headers: { 'Content-Type': 'application/json' },
    status: 200,
    ...init,
  })
}

describe('shared api http client', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns parsed json for successful GET requests', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }))

    await expect(getJson<{ ok: boolean }>('/api/status')).resolves.toEqual({ ok: true })
  })

  it('serializes JSON payloads for POST requests', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ saved: true }))

    await postJson('/api/profiles', { slug: 'test' })

    const [, init] = fetchMock.mock.calls[0]
    expect(init?.method).toBe('POST')
    expect(new Headers(init?.headers).get('Content-Type')).toBe('application/json')
    expect(init?.body).toBe(JSON.stringify({ slug: 'test' }))
  })

  it('uses DELETE for deleteJson requests', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ deleted: true }))

    await deleteJson('/api/profiles/example')

    const [, init] = fetchMock.mock.calls[0]
    expect(init?.method).toBe('DELETE')
  })

  it('raises ApiError with backend error messages', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ error: 'forbidden' }, { status: 403 }))

    await expect(getJson('/api/profiles')).rejects.toEqual(new ApiError(403, 'forbidden'))
  })
})
