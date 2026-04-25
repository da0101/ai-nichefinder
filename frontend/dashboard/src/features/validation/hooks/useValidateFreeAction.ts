import { useState } from 'react'

import type { ValidateFreeResponse } from '@/types/api'
import { toErrorMessage } from '@/shared/api/http'

import { runValidateFree } from '../api'

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
      const json = await runValidateFree({ profile, keyword })
      setData(json)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error))
      throw error
    } finally {
      setRunning(false)
    }
  }

  return { data, running, error, run }
}
