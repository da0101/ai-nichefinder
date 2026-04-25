import type { KeywordDetailResponse } from '@/types/api'
import { getJson } from '@/shared/api/http'

export function fetchKeywordDetail(id: string, signal: AbortSignal): Promise<KeywordDetailResponse> {
  return getJson<KeywordDetailResponse>(`/api/keywords/${id}`, { signal })
}
