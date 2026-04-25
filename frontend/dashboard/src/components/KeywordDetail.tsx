import { FileText, Globe } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { ScoreBreakdown } from './ScoreBreakdown'
import { cn, priorityBadgeClass, scoreColorClass } from '@/lib/utils'
import type { KeywordDetailResponse } from '@/types/api'

interface Props {
  data: KeywordDetailResponse | null
  loading: boolean
  error: string | null
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[160px_1fr] gap-2 border-b border-slate-100 py-2 last:border-0">
      <span className="text-[13px] font-medium text-slate-500">{label}</span>
      <span className="text-[13px] text-slate-800">{value || '\u2014'}</span>
    </div>
  )
}

export function KeywordDetail({ data, loading, error }: Props) {
  if (error) {
    return (
      <div className="flex h-full items-center justify-center text-red-500 text-sm">{error}</div>
    )
  }

  if (loading || !data) {
    return (
      <div className="space-y-4 p-6">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  const { keyword, score_breakdown: bd, serp, brief } = data
  const score = keyword.score ?? 0
  const competition = serp?.competition ?? {}

  return (
    <div className="space-y-4 p-6">
      {/* Title */}
      <h2 className="text-xl font-bold text-slate-900">{keyword.term}</h2>

      {/* Opportunity score */}
      {bd && (
        <Card>
          <CardHeader><CardTitle>Opportunity Score</CardTitle></CardHeader>
          <CardContent>
            <div className="mb-5 text-center">
              <div className={cn('font-mono text-5xl font-bold leading-none', scoreColorClass(score))}>
                {Math.round(score)}
                <span className="text-xl text-slate-400">/100</span>
              </div>
              <div className="mt-3">
                <span
                  className={cn(
                    'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold',
                    priorityBadgeClass(bd.priority)
                  )}
                >
                  {(bd.priority ?? 'unknown').toUpperCase()} PRIORITY
                </span>
              </div>
            </div>
            <Separator className="mb-5" />
            <ScoreBreakdown breakdown={bd} />
          </CardContent>
        </Card>
      )}

      {/* Recommendation */}
      {bd && (
        <Card>
          <CardHeader><CardTitle>Recommendation</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-start gap-3">
              <Badge
                variant={
                  bd.action === 'new_article'
                    ? 'default'
                    : bd.action === 'rewrite_existing'
                    ? 'warning'
                    : 'secondary'
                }
                className="text-sm"
              >
                {bd.action === 'new_article'
                  ? 'Write new article'
                  : bd.action === 'rewrite_existing'
                  ? 'Rewrite existing'
                  : 'Skip for now'}
              </Badge>
              {bd.why && (
                <p className="text-[13px] leading-relaxed text-slate-500">{bd.why}</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Keyword details */}
      <Card>
        <CardHeader><CardTitle>Keyword Details</CardTitle></CardHeader>
        <CardContent>
          <DetailRow label="Search Intent" value={keyword.intent} />
          <DetailRow label="Trend" value={keyword.trend} />
          <DetailRow
            label="Monthly Searches"
            value={
              keyword.volume != null ? (
                <span className="font-mono">{keyword.volume.toLocaleString()}</span>
              ) : null
            }
          />
          <DetailRow
            label="SEO Difficulty"
            value={
              keyword.difficulty != null ? (
                <span className="font-mono">{keyword.difficulty}/100</span>
              ) : null
            }
          />
          <DetailRow
            label="Can You Rank?"
            value={
              competition.rankable != null
                ? competition.rankable
                  ? 'Yes'
                  : 'No \u2014 high-authority sites dominate'
                : null
            }
          />
          <DetailRow
            label="Competition Level"
            value={competition.competition_level}
          />
          <DetailRow label="Discovered" value={keyword.discovered_at?.slice(0, 10)} />
        </CardContent>
      </Card>

      {/* Content brief */}
      {brief && (
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-amber-700">
              <FileText className="h-3.5 w-3.5" />
              Content Brief
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-[15px] font-bold text-slate-900">{brief.title}</p>
            <div className="grid grid-cols-2 gap-2 text-[13px] text-slate-700">
              <div><span className="font-medium">Format: </span>{brief.content_type}</div>
              <div><span className="font-medium">Tone: </span>{brief.tone}</div>
              <div><span className="font-medium">Length: </span>{brief.word_count_target} words</div>
            </div>
            {brief.suggested_h2_structure && brief.suggested_h2_structure.length > 0 && (
              <ul className="mt-3 space-y-1">
                {brief.suggested_h2_structure.map((h, i) => (
                  <li key={i} className="flex items-start gap-2 text-[13px] text-slate-700">
                    <span className="mt-0.5 font-mono text-[10px] text-amber-600">{i + 1}.</span>
                    {h}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}

      {/* SERP pages */}
      {serp && serp.pages.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5" />
              Who Currently Ranks (top {Math.min(5, serp.pages.length)})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {serp.pages.slice(0, 5).map((page, i) => (
              <div key={i} className="border-b border-slate-100 px-5 py-3 last:border-0">
                <div className="flex items-start gap-2">
                  <span className="mt-0.5 font-mono text-[12px] text-slate-400">
                    #{page.position ?? i + 1}
                  </span>
                  <div className="min-w-0">
                    <p className="text-[13px] font-semibold text-slate-800 leading-snug">
                      {page.title || '\u2014'}
                    </p>
                    {page.url && (
                      <a
                        href={page.url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-0.5 block truncate text-[11px] text-indigo-600 hover:underline"
                      >
                        {page.url}
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
