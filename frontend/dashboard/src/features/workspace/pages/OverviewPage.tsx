import { ArrowRight, Database, FolderOpenDot, ShieldCheck, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

import { StatsBar } from '@/components/StatsBar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useWorkspace } from '@/features/workspace/context/WorkspaceContext'
import { scoreBadgeClass } from '@/lib/utils'
import { PageHeader } from '../components/PageHeader'
import { WorkspaceOverview } from '../components/WorkspaceOverview'

export function OverviewPage() {
  const {
    activeProfile,
    availableProfiles,
    dashboardData,
    dashboardError,
    dashboardLoading,
    sortedKeywords,
    validationRunning,
  } = useWorkspace()

  if (dashboardError && !dashboardData) {
    return <ErrorCard title="Could not load workspace data" detail={dashboardError} />
  }

  const activeSummary =
    availableProfiles.find(profile => profile.slug === activeProfile) ??
    availableProfiles[0]
  const recentArticles = dashboardData?.articles.slice(0, 5) ?? []
  const topKeywords = sortedKeywords.slice(0, 6)

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Workspace"
        title="Overview"
        description="Monitor opportunity flow, storage boundaries, and recent output for the active business."
        meta={
          <>
            <Badge variant="outline">{activeProfile}</Badge>
            <Badge variant="secondary">{sortedKeywords.length} queued</Badge>
          </>
        }
      />

      <section className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <WorkspaceOverview
          activeProfile={activeProfile}
          databasePath={dashboardData?.paths.database ?? 'No database loaded'}
          articlesPath={dashboardData?.paths.articles_dir ?? 'No articles directory loaded'}
          keywordCount={sortedKeywords.length}
          validationRunning={validationRunning}
        />
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Quick Actions</CardTitle>
            <p className="mt-2 text-sm text-slate-600">
              Move through the operator workflow without hunting for panels.
            </p>
          </CardHeader>
          <CardContent className="space-y-2">
            <QuickLink to="/research" label="Run new validation" hint="Launch validate-free from the browser" />
            <QuickLink to="/explorer" label="Inspect keyword queue" hint="Review rankability and brief context" />
            <QuickLink to="/profiles" label="Manage businesses" hint="Create or prune isolated profile workspaces" />
          </CardContent>
        </Card>
      </section>

      <StatsBar data={dashboardData} />

      <section className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle>Highest-Value Opportunities</CardTitle>
                <p className="mt-2 text-sm text-slate-600">
                  Current top terms for <span className="font-medium text-slate-900">{activeProfile}</span>.
                </p>
              </div>
              <Badge variant="outline">{topKeywords.length}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {dashboardLoading && !dashboardData ? (
              <p className="text-sm text-slate-400">Loading opportunities...</p>
            ) : topKeywords.length > 0 ? (
              topKeywords.map(keyword => (
                <Link
                  key={keyword.id}
                  to="/explorer"
                  className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-slate-900">{keyword.term}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {keyword.intent ?? 'unknown intent'} | {keyword.trend ?? 'unknown trend'}
                    </div>
                  </div>
                  <span className={`rounded-md px-2 py-1 text-xs font-semibold ${scoreBadgeClass(keyword.score)}`}>
                    {Math.round(keyword.score ?? 0)}
                  </span>
                </Link>
              ))
            ) : (
              <p className="rounded-lg border border-dashed border-slate-200 px-4 py-6 text-sm text-slate-500">
                No keyword opportunities yet. Start with the Research Ops page.
              </p>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Active Business Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <MetricTile
                icon={Database}
                label="Approved noise"
                value={activeSummary?.approved_noise ?? 0}
              />
              <MetricTile
                icon={ShieldCheck}
                label="Approved validity"
                value={activeSummary?.approved_validity ?? 0}
              />
              <MetricTile
                icon={Sparkles}
                label="Trusted domains"
                value={activeSummary?.approved_legitimacy ?? 0}
              />
              <MetricTile
                icon={FolderOpenDot}
                label="Drafted articles"
                value={dashboardData?.summary.articles ?? 0}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle>Recent Articles</CardTitle>
                  <p className="mt-2 text-sm text-slate-600">Newest content artifacts in the active workspace.</p>
                </div>
                <Badge variant="outline">{recentArticles.length}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {recentArticles.length > 0 ? (
                recentArticles.map(article => (
                  <div
                    key={article.id}
                    className="rounded-lg border border-slate-200 px-4 py-3"
                  >
                    <div className="truncate text-sm font-medium text-slate-900">
                      {article.title ?? 'Untitled article'}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {article.status ?? 'unknown'} | {article.created_at?.slice(0, 10) ?? 'no date'}
                    </div>
                  </div>
                ))
              ) : (
                <p className="rounded-lg border border-dashed border-slate-200 px-4 py-6 text-sm text-slate-500">
                  No articles drafted yet.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}

function QuickLink({
  to,
  label,
  hint,
}: {
  to: string
  label: string
  hint: string
}) {
  return (
    <Button asChild variant="outline" className="h-auto w-full justify-between rounded-lg px-4 py-3">
      <Link to={to}>
        <span className="text-left">
          <span className="block text-sm font-medium text-slate-900">{label}</span>
          <span className="block text-xs text-slate-500">{hint}</span>
        </span>
        <ArrowRight className="h-4 w-4 text-slate-400" />
      </Link>
    </Button>
  )
}

function MetricTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Database
  label: string
  value: number
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center gap-2 text-slate-500">
        <Icon className="h-4 w-4" />
        <span className="text-xs font-semibold uppercase tracking-[0.18em]">{label}</span>
      </div>
      <div className="mt-3 font-mono text-2xl font-semibold text-slate-900">{value}</div>
    </div>
  )
}

function ErrorCard({ title, detail }: { title: string; detail: string }) {
  return (
    <Card className="border-red-200 bg-red-50">
      <CardHeader>
        <CardTitle className="text-red-700">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-red-700">{detail}</p>
      </CardContent>
    </Card>
  )
}
