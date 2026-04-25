import type { FinalReviewResponse, TrainingApprovalRequest, TrainingReviewResponse } from '@/types/api'
import { getJson, postJson } from '@/shared/api/http'

export function fetchTrainingReview(profile: string): Promise<TrainingReviewResponse> {
  return getJson<TrainingReviewResponse>(`/api/training-review?profile=${encodeURIComponent(profile)}`)
}

export function approveTraining(payload: TrainingApprovalRequest): Promise<TrainingReviewResponse> {
  return postJson<TrainingReviewResponse>('/api/training-approve', payload)
}

export function fetchFinalReview(profiles: string[]): Promise<FinalReviewResponse> {
  const query = encodeURIComponent(profiles.join(','))
  return getJson<FinalReviewResponse>(`/api/final-review?profiles=${query}`)
}
