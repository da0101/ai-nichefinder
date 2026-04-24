import { useState } from 'react'
import type { ValidateFreeResponse } from '@/types/api'

interface UseValidateFreeActionResult {
  data: ValidateFreeResponse | null
  running: boolean
  error: string | null
  run: (profile: string, keyword: string) => Promise<void>
}

export function useValidateFreeAction(): UseValidateFreeActionResult {
  const [data, setData] = useState<ValidateFreeResponse | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(profile: string, keyword: string) {
    setRunning(true)
    try {
      const response = await fetch('/api/validate-free', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile, keyword }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${response.status}`)
      }
      const json: ValidateFreeResponse = await response.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      throw e
    } finally {
      setRunning(false)
    }
  }

  return { data, running, error, run }
}
