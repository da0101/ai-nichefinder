export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unknown error'
}

export async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  return requestJson<T>(path, init)
}

export async function postJson<T>(path: string, body?: unknown, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }
  return requestJson<T>(path, {
    ...init,
    method: 'POST',
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export async function deleteJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  return requestJson<T>(path, { ...init, method: 'DELETE' })
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) {
    throw await buildApiError(response)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

async function buildApiError(response: Response): Promise<ApiError> {
  const fallback = `HTTP ${response.status}`
  try {
    const payload = (await response.json()) as { error?: unknown }
    if (typeof payload.error === 'string' && payload.error.trim()) {
      return new ApiError(response.status, payload.error)
    }
  } catch {
    // Ignore malformed error bodies and return the fallback message.
  }
  return new ApiError(response.status, fallback)
}
