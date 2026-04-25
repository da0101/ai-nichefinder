import { createContext, useCallback, useContext, useMemo } from 'react'

import { useDashboard } from '@/features/dashboard/hooks/useDashboard'
import { useProfiles } from '@/features/profiles/hooks/useProfiles'
import { useFinalReview } from '@/features/reviews/hooks/useFinalReview'
import { useTrainingReview } from '@/features/reviews/hooks/useTrainingReview'
import { useValidateFreeAction } from '@/features/validation/hooks/useValidateFreeAction'
import type {
  KeywordSummary,
  ProfileSummary,
  SiteConfigDto,
  TrainingCandidate,
} from '@/types/api'

interface WorkspaceContextValue {
  dashboardData: ReturnType<typeof useDashboard>['data']
  dashboardLoading: boolean
  dashboardError: string | null
  lastUpdated: Date | null
  sortedKeywords: KeywordSummary[]
  refreshDashboard: () => Promise<void>
  refreshWorkspace: () => Promise<void>
  activeProfile: string
  availableProfiles: ProfileSummary[]
  profilesLoading: boolean
  profilesRefreshing: boolean
  profilesError: string | null
  clearProfilesError: () => void
  switchProfile: (profile: string) => Promise<void>
  createProfile: (input: { slug: string; siteConfig: SiteConfigDto; use?: boolean }) => Promise<void>
  updateProfile: (profile: string, siteConfig: SiteConfigDto) => Promise<void>
  deleteProfile: (profile: string) => Promise<void>
  trainingReview: ReturnType<typeof useTrainingReview>['data']
  trainingLoading: boolean
  trainingError: string | null
  approvingTraining: boolean
  finalReview: ReturnType<typeof useFinalReview>['data']
  finalReviewLoading: boolean
  finalReviewError: string | null
  validationRun: ReturnType<typeof useValidateFreeAction>['data']
  validationRunning: boolean
  validationError: string | null
  runValidation: (profile: string, keyword: string) => Promise<void>
  approveCandidate: (candidate: TrainingCandidate) => Promise<void>
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null)

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const {
    data: dashboardData,
    loading: dashboardLoading,
    error: dashboardError,
    lastUpdated,
    refresh: refreshDashboard,
  } = useDashboard()
  const {
    data: profilesData,
    loading: profilesLoading,
    error: profilesError,
    refreshing: profilesRefreshing,
    clearError: clearProfilesError,
    refresh: refreshProfiles,
    switchProfile: switchProfileRequest,
    createProfile: createProfileRequest,
    updateProfile: updateProfileRequest,
    deleteProfile: deleteProfileRequest,
  } = useProfiles()

  const activeProfile = profilesData?.active_profile ?? 'default'
  const availableProfiles = profilesData?.profiles ?? []
  const sortedKeywords = useMemo(
    () =>
      dashboardData
        ? [...dashboardData.keywords].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
        : [],
    [dashboardData],
  )
  const finalReviewProfiles = useMemo(() => {
    const explicit = availableProfiles
      .filter(profile => profile.slug !== 'default')
      .map(profile => profile.slug)
    return explicit.length > 0 ? explicit : ['default']
  }, [availableProfiles])

  const {
    data: trainingReview,
    loading: trainingLoading,
    error: trainingError,
    approving: approvingTraining,
    refresh: refreshTraining,
    approve,
  } = useTrainingReview(activeProfile)
  const {
    data: finalReview,
    loading: finalReviewLoading,
    error: finalReviewError,
    refresh: refreshFinalReview,
  } = useFinalReview(finalReviewProfiles)
  const {
    data: validationRun,
    running: validationRunning,
    error: validationError,
    run: runValidation,
  } = useValidateFreeAction()

  const refreshWorkspace = useCallback(async () => {
    await Promise.all([
      refreshDashboard(),
      refreshProfiles(),
      refreshTraining(),
      refreshFinalReview(),
    ])
  }, [refreshDashboard, refreshProfiles, refreshTraining, refreshFinalReview])

  const switchProfile = useCallback(
    async (profile: string) => {
      await switchProfileRequest(profile)
      await Promise.all([refreshDashboard(), refreshProfiles(), refreshFinalReview()])
    },
    [refreshDashboard, refreshFinalReview, refreshProfiles, switchProfileRequest],
  )

  const createProfile = useCallback(
    async (input: { slug: string; siteConfig: SiteConfigDto; use?: boolean }) => {
      const payload = {
        slug: input.slug,
        siteConfig: input.siteConfig,
        use: input.use,
      }
      await createProfileRequest(payload)
      await Promise.all([refreshDashboard(), refreshProfiles(), refreshFinalReview()])
    },
    [createProfileRequest, refreshDashboard, refreshFinalReview, refreshProfiles],
  )

  const updateProfile = useCallback(
    async (profile: string, siteConfig: SiteConfigDto) => {
      await updateProfileRequest(profile, siteConfig)
      await Promise.all([refreshDashboard(), refreshProfiles()])
    },
    [refreshDashboard, refreshProfiles, updateProfileRequest],
  )

  const deleteProfile = useCallback(
    async (profile: string) => {
      await deleteProfileRequest(profile)
      await Promise.all([refreshDashboard(), refreshProfiles(), refreshFinalReview()])
    },
    [deleteProfileRequest, refreshDashboard, refreshFinalReview, refreshProfiles],
  )

  const approveCandidate = useCallback(
    async (candidate: TrainingCandidate) => {
      await approve({
        profile: activeProfile,
        noise_keyword_phrases:
          candidate.label === 'noise' && candidate.scope === 'keyword_phrase'
            ? [candidate.value]
            : undefined,
        noise_secondary_phrases:
          candidate.label === 'noise' && candidate.scope === 'secondary_phrase'
            ? [candidate.value]
            : undefined,
        noise_domains:
          candidate.label === 'noise' && candidate.scope === 'domain'
            ? [candidate.value]
            : undefined,
        valid_keyword_phrases:
          candidate.label === 'validity' && candidate.scope === 'keyword_phrase'
            ? [candidate.value]
            : undefined,
        valid_secondary_phrases:
          candidate.label === 'validity' && candidate.scope === 'secondary_phrase'
            ? [candidate.value]
            : undefined,
        trusted_domains:
          candidate.label === 'legitimacy' && candidate.scope === 'domain'
            ? [candidate.value]
            : undefined,
      })
      await Promise.all([refreshProfiles(), refreshFinalReview()])
    },
    [activeProfile, approve, refreshFinalReview, refreshProfiles],
  )

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      dashboardData,
      dashboardLoading,
      dashboardError,
      lastUpdated,
      sortedKeywords,
      refreshDashboard,
      refreshWorkspace,
      activeProfile,
      availableProfiles,
      profilesLoading,
      profilesRefreshing,
      profilesError,
      clearProfilesError,
      switchProfile,
      createProfile,
      updateProfile,
      deleteProfile,
      trainingReview,
      trainingLoading,
      trainingError,
      approvingTraining,
      finalReview,
      finalReviewLoading,
      finalReviewError,
      validationRun,
      validationRunning,
      validationError,
      runValidation,
      approveCandidate,
    }),
    [
      activeProfile,
      approveCandidate,
      approvingTraining,
      availableProfiles,
      clearProfilesError,
      createProfile,
      dashboardData,
      dashboardError,
      dashboardLoading,
      deleteProfile,
      finalReview,
      finalReviewError,
      finalReviewLoading,
      lastUpdated,
      profilesError,
      profilesLoading,
      profilesRefreshing,
      refreshDashboard,
      refreshWorkspace,
      runValidation,
      sortedKeywords,
      switchProfile,
      trainingError,
      trainingLoading,
      trainingReview,
      updateProfile,
      validationError,
      validationRun,
      validationRunning,
    ],
  )

  return (
    <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext)
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider')
  }
  return context
}
