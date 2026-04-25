import { useEffect, useMemo, useState } from 'react'

import { KeywordDetail } from '@/components/KeywordDetail'
import { KeywordList } from '@/components/KeywordList'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useKeywordDetail } from '@/features/keywords/hooks/useKeywordDetail'
import { useWorkspace } from '@/features/workspace/context/WorkspaceContext'
import { PageHeader } from '../components/PageHeader'

export function KeywordExplorerPage() {
  const {
    activeProfile,
    dashboardData,
    dashboardError,
    dashboardLoading,
    sortedKeywords,
  } = useWorkspace()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    setSelectedId(null)
  }, [activeProfile])

  const resolvedId = useMemo(
    () => selectedId ?? (sortedKeywords.length > 0 ? sortedKeywords[0].id : null),
    [selectedId, sortedKeywords],
  )
  const {
    data: detail,
    loading: detailLoading,
    error: detailError,
  } = useKeywordDetail(resolvedId)

  if (dashboardError && !dashboardData) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-700">Could not load keyword explorer</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-700">{dashboardError}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Workspace"
        title="Keyword Explorer"
        description="Inspect the ranked queue, compare opportunity scores, and drill into SERP evidence without leaving the active business context."
        meta={
          <>
            <Badge variant="outline">{activeProfile}</Badge>
            <Badge variant="secondary">{sortedKeywords.length} queued</Badge>
          </>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Card className="overflow-hidden xl:sticky xl:top-20 xl:max-h-[calc(100vh-8rem)]">
          <CardHeader className="border-b border-slate-100">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>Keyword Queue</CardTitle>
                <p className="mt-2 text-sm text-slate-600">Prioritized by current opportunity score.</p>
              </div>
              {resolvedId && <Badge variant="outline">Live selection</Badge>}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {dashboardLoading && !dashboardData ? (
              <div className="flex h-48 items-center justify-center text-sm text-slate-400">
                Loading...
              </div>
            ) : (
              <div className="max-h-[calc(100vh-13rem)] overflow-y-auto">
                <KeywordList
                  keywords={sortedKeywords}
                  selectedId={resolvedId}
                  onSelect={id => setSelectedId(id)}
                />
              </div>
            )}
          </CardContent>
        </Card>

        <section className="min-w-0">
          {resolvedId ? (
            <KeywordDetail data={detail} loading={detailLoading} error={detailError} />
          ) : (
            <Card>
              <CardContent className="flex h-64 items-center justify-center text-sm text-slate-400">
                Select a keyword to see its analysis.
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </div>
  )
}
