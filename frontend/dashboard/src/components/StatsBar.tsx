import type { DashboardResponse } from '@/types/api'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

interface Props {
  data: DashboardResponse | null
}

const STATS = [
  { key: 'total_keywords' as const, label: 'Keywords found' },
  { key: 'briefed_keywords' as const, label: 'Briefs ready' },
  { key: 'articles' as const, label: 'Articles drafted' },
  { key: 'published_articles' as const, label: 'Published' },
]

export function StatsBar({ data }: Props) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {STATS.map(({ key, label }) => (
        <Card key={key}>
          <CardContent className="px-5 py-4">
            {data ? (
              <span className="font-mono text-3xl font-bold text-slate-900">
                {data.summary[key]}
              </span>
            ) : (
              <Skeleton className="h-8 w-12" />
            )}
            <div className="mt-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
