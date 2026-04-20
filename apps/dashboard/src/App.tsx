import { useMemo, useState } from 'react'
import { TrendingUp } from 'lucide-react'
import { useDashboard } from '@/hooks/useDashboard'
import { useKeywordDetail } from '@/hooks/useKeywordDetail'
import { StatsBar } from '@/components/StatsBar'
import { LiveIndicator } from '@/components/LiveIndicator'
import { KeywordList } from '@/components/KeywordList'
import { KeywordDetail } from '@/components/KeywordDetail'

export default function App() {
  const { data, loading: dashLoading, error: dashError, lastUpdated, refresh } = useDashboard()
  const [selectedId, setSelectedId] = useState<string | null>(null)

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

  if (dashError && !data) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <p className="text-base font-semibold text-red-600">Could not load data</p>
          <p className="mt-1 text-sm text-slate-500">{dashError}</p>
          <p className="mt-2 text-xs text-slate-400">Run <code className="font-mono">seo db init</code> first if the database is missing.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-50 font-sans">
      {/* Header */}
      <header className="flex flex-shrink-0 items-center justify-between border-b border-blue-800 bg-blue-700 px-6 py-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-200" />
          <div>
            <h1 className="text-[16px] font-bold text-white">Nichefinder</h1>
            <p className="text-[11px] text-blue-300">SEO Research Dashboard</p>
          </div>
        </div>
        <LiveIndicator lastUpdated={lastUpdated} onRefresh={refresh} />
      </header>

      {/* Stats */}
      <StatsBar data={data} />

      {/* Main: sidebar + detail */}
      <div className="flex min-h-0 flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="flex w-72 flex-shrink-0 flex-col border-r border-slate-200 bg-white">
          {dashLoading && !data ? (
            <div className="flex h-full items-center justify-center text-sm text-slate-400">
              Loading\u2026
            </div>
          ) : (
            <KeywordList
              keywords={sortedKeywords}
              selectedId={resolvedId}
              onSelect={id => setSelectedId(id)}
            />
          )}
        </aside>

        {/* Detail pane */}
        <main className="flex-1 overflow-y-auto">
          {resolvedId ? (
            <KeywordDetail data={detail} loading={detailLoading} error={detailError} />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-slate-400">
              Select a keyword to see its analysis.
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
