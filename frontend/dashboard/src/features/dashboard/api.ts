import type { DashboardResponse } from '@/types/api'
import { getJson } from '@/shared/api/http'

export function fetchDashboard(signal?: AbortSignal): Promise<DashboardResponse> {
  return getJson<DashboardResponse>('/api/dashboard', signal ? { signal } : undefined)
}
