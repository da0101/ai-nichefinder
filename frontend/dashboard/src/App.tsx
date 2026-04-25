import { useEffect, useMemo, useState } from 'react'
import { BarChart3, FlaskConical, TrendingUp } from 'lucide-react'
import { useDashboard } from '@/features/dashboard/hooks/useDashboard'
import { useKeywordDetail } from '@/features/keywords/hooks/useKeywordDetail'
import { useProfiles } from '@/features/profiles/hooks/useProfiles'
import { useTrainingReview } from '@/features/reviews/hooks/useTrainingReview'
import { useFinalReview } from '@/features/reviews/hooks/useFinalReview'
import { useValidateFreeAction } from '@/features/validation/hooks/useValidateFreeAction'
import { StatsBar } from '@/components/StatsBar'
import { LiveIndicator } from '@/components/LiveIndicator'
import { KeywordList } from '@/components/KeywordList'
import { KeywordDetail } from '@/components/KeywordDetail'
import { ProfileSwitcher } from '@/components/ProfileSwitcher'
import { TrainingReviewPanel } from '@/components/TrainingReviewPanel'
import { FinalReviewPanel } from '@/components/FinalReviewPanel'
import { ProfileConfigPanel } from '@/components/ProfileConfigPanel'
import { ValidationLabPanel } from '@/components/ValidationLabPanel'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { TrainingCandidate } from '@/types/api'

type DashboardView = 'workspace' | 'explorer'

export default function App() {
  const { data, loading: dashLoading, error: dashError, lastUpdated, refresh } = useDashboard()
  const {
    data: profilesData,
    loading: profilesLoading,
    error: profilesError,
    refreshing: profilesRefreshing,
    clearError: clearProfilesError,
    refresh: refreshProfiles,
    switchProfile,
    createProfile,
    updateProfile,
    deleteProfile,
  } = useProfiles()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [reviewProfile, setReviewProfile] = useState<string | null>(null)
  const [view, setView] = useState<DashboardView>('workspace')

  const sortedKeywords = useMemo(
    () =>
      data
        ? [...data.keywords].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
        : [],
    [data]
  )

  const resolvedId =
    selectedId ?? (sortedKeywords.length > 0 ? sortedKeywords[0].id : null)

  const { data: detail, loading: detailLoading, error: detailError } = useKeywordDetail(resolvedId)
  const activeProfile = profilesData?.active_profile ?? 'default'
  const availableProfiles = profilesData?.profiles ?? []
  const finalReviewProfiles = useMemo(() => {
    const explicit = availableProfiles.filter(profile => profile.slug !== 'default').map(profile => profile.slug)
    return explicit.length > 0 ? explicit : ['default']
  }, [availableProfiles])
  const { data: trainingReview, loading: trainingLoading, error: trainingError, approving, approve } = useTrainingReview(reviewProfile ?? activeProfile)
  const { data: finalReview, loading: finalReviewLoading, error: finalReviewError } = useFinalReview(finalReviewProfiles)
  const { data: validationRun, running: validationRunning, error: validationError, run: runValidation } = useValidateFreeAction()

  useEffect(() => {
    setReviewProfile(activeProfile)
  }, [activeProfile])

  async function handleProfileChange(profile: string) {
    await switchProfile(profile)
    setSelectedId(null)
    await Promise.all([refresh(), refreshProfiles()])
  }

  async function handleApprove(candidate: TrainingCandidate) {
    const payload = {
      profile: reviewProfile ?? activeProfile,
      noise_keyword_phrases: candidate.label === 'noise' && candidate.scope === 'keyword_phrase' ? [candidate.value] : undefined,
      noise_secondary_phrases: candidate.label === 'noise' && candidate.scope === 'secondary_phrase' ? [candidate.value] : undefined,
      noise_domains: candidate.label === 'noise' && candidate.scope === 'domain' ? [candidate.value] : undefined,
      valid_keyword_phrases: candidate.label === 'validity' && candidate.scope === 'keyword_phrase' ? [candidate.value] : undefined,
      valid_secondary_phrases: candidate.label === 'validity' && candidate.scope === 'secondary_phrase' ? [candidate.value] : undefined,
      trusted_domains: candidate.label === 'legitimacy' && candidate.scope === 'domain' ? [candidate.value] : undefined,
    }
    await approve(payload)
    await refreshProfiles()
  }

  if (dashError && !data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <p className="text-base font-semibold text-red-600">Could not load data</p>
          <p className="mt-1 text-sm text-slate-500">{dashError}</p>
          <p className="mt-2 text-xs text-slate-400">Run <code className="font-mono">seo db init</code> first if the database is missing.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-100 font-sans text-slate-900">
      <header className="sticky top-0 z-40 border-b border-blue-900/80 bg-gradient-to-r from-blue-900 via-blue-800 to-blue-700 shadow-sm">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-white/10 p-2 ring-1 ring-white/15">
              <TrendingUp className="h-5 w-5 text-blue-100" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Nichefinder</h1>
              <p className="text-xs text-blue-100/80">SEO research workspace for profiles, training loops, and keyword validation.</p>
            </div>
          </div>
          <LiveIndicator lastUpdated={lastUpdated} onRefresh={refresh} />
        </div>
      </header>

      <div className="mx-auto flex max-w-[1600px] flex-col gap-6 px-4 py-5 sm:px-6">
        <StatsBar data={data} />

        <section className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <ProfileSwitcher
            activeProfile={activeProfile}
            profiles={availableProfiles}
            loading={profilesLoading || profilesRefreshing}
            error={null}
            onChange={profile => void handleProfileChange(profile)}
          />
          <WorkspaceOverview
            activeProfile={activeProfile}
            databasePath={data?.paths.database ?? 'No database loaded'}
            articlesPath={data?.paths.articles_dir ?? 'No articles directory loaded'}
            keywordCount={sortedKeywords.length}
            validationRunning={validationRunning}
          />
        </section>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Workspace</h2>
              <p className="mt-1 text-sm text-slate-600">Switch between operating the profile and inspecting the current keyword bank.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <TabButton
                active={view === 'workspace'}
                icon={FlaskConical}
                title="Research Ops"
                description="Profiles, training review, validation runs"
                onClick={() => setView('workspace')}
              />
              <TabButton
                active={view === 'explorer'}
                icon={BarChart3}
                title="Keyword Explorer"
                description="Prioritized list, SERP detail, content brief"
                onClick={() => setView('explorer')}
              />
            </div>
          </div>

          {view === 'workspace' ? (
            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
              <div className="space-y-4">
                <ProfileConfigPanel
                  profiles={availableProfiles}
                  activeProfile={activeProfile}
                  loading={profilesLoading}
                  saving={profilesRefreshing}
                  error={profilesError}
                  onDismissError={clearProfilesError}
                  onSwitchProfile={profile => void handleProfileChange(profile)}
                  onSaveProfile={(profile, siteConfig) => void updateProfile(profile, siteConfig)}
                  onCreateProfile={input => void createProfile(input)}
                  onDeleteProfile={profile => void deleteProfile(profile)}
                />
                <FinalReviewPanel
                  data={finalReview}
                  loading={finalReviewLoading}
                  error={finalReviewError}
                />
              </div>
              <div className="space-y-4">
                <ValidationLabPanel
                  profile={reviewProfile ?? activeProfile}
                  data={validationRun}
                  running={validationRunning}
                  error={validationError}
                  onRun={(profile, keyword) => void runValidation(profile, keyword)}
                />
                <TrainingReviewPanel
                  data={trainingReview}
                  loading={trainingLoading}
                  error={trainingError}
                  approving={approving}
                  onApprove={candidate => void handleApprove(candidate)}
                />
              </div>
            </div>
          ) : (
            <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
              <Card className="overflow-hidden xl:sticky xl:top-24 xl:max-h-[calc(100vh-7rem)]">
                <CardHeader className="border-b border-slate-100">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <CardTitle className="text-slate-500">Keyword Queue</CardTitle>
                      <p className="mt-1 text-sm text-slate-600">
                        Highest-opportunity keywords for <span className="font-medium text-slate-900">{activeProfile}</span>.
                      </p>
                    </div>
                    <Badge variant="outline">{sortedKeywords.length}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {dashLoading && !data ? (
                    <div className="flex h-48 items-center justify-center text-sm text-slate-400">
                      Loading…
                    </div>
                  ) : (
                    <div className="max-h-[calc(100vh-14rem)] overflow-y-auto">
                      <KeywordList
                        keywords={sortedKeywords}
                        selectedId={resolvedId}
                        onSelect={id => setSelectedId(id)}
                      />
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="overflow-hidden">
                <CardHeader className="border-b border-slate-100">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <CardTitle className="text-slate-500">Keyword Detail</CardTitle>
                      <p className="mt-1 text-sm text-slate-600">
                        Inspect score breakdown, SERP context, and brief recommendations.
                      </p>
                    </div>
                    {resolvedId && <Badge variant="secondary">Live selection</Badge>}
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {resolvedId ? (
                    <KeywordDetail data={detail} loading={detailLoading} error={detailError} />
                  ) : (
                    <div className="flex h-64 items-center justify-center text-sm text-slate-400">
                      Select a keyword to see its analysis.
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function WorkspaceOverview({
  activeProfile,
  databasePath,
  articlesPath,
  keywordCount,
  validationRunning,
}: {
  activeProfile: string
  databasePath: string
  articlesPath: string
  keywordCount: number
  validationRunning: boolean
}) {
  return (
    <Card className="border-blue-200 bg-gradient-to-br from-white to-blue-50/50">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-blue-700">Active Workspace</CardTitle>
            <p className="mt-1 text-sm text-slate-700">
              Manage the <span className="font-semibold text-slate-900">{activeProfile}</span> profile, review learned signals, and run new validations from one surface.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{keywordCount} keywords</Badge>
            {validationRunning && <Badge variant="warning">Validation running</Badge>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2">
        <InfoStrip label="Database" value={databasePath} />
        <InfoStrip label="Articles" value={articlesPath} />
      </CardContent>
    </Card>
  )
}

function InfoStrip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white/90 px-4 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</div>
      <div className="mt-2 break-all font-mono text-xs text-slate-700">{value}</div>
    </div>
  )
}

function TabButton({
  active,
  icon: Icon,
  title,
  description,
  onClick,
}: {
  active: boolean
  icon: typeof FlaskConical
  title: string
  description: string
  onClick: () => void
}) {
  return (
    <Button
      type="button"
      variant={active ? 'default' : 'outline'}
      className="h-auto min-w-[210px] justify-start rounded-xl px-4 py-3 text-left"
      onClick={onClick}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="flex min-w-0 flex-col">
        <span className="text-sm font-semibold">{title}</span>
        <span className={`text-xs ${active ? 'text-blue-100' : 'text-slate-500'}`}>{description}</span>
      </span>
    </Button>
  )
}
