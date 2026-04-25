import type { ValidateFreeRequest, ValidateFreeResponse } from '@/types/api'
import { postJson } from '@/shared/api/http'

export function runValidateFree(payload: ValidateFreeRequest): Promise<ValidateFreeResponse> {
  return postJson<ValidateFreeResponse>('/api/validate-free', payload)
}
