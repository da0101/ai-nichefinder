import type { DashboardResponse } from '@/types/api'
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
    <div className="flex border-b border-slate-200 bg-white">
      {STATS.map(({ key, label }, i) => (
        <div
          key={key}
          className={`flex flex-col px-6 py-3 ${i < STATS.length - 1 ? 'border-r border-slate-200' : ''}`}
        >
          {data ? (
            <span className="font-mono text-2xl font-bold text-blue-700">
              {data.summary[key]}
            </span>
          ) : (
            <Skeleton className="h-7 w-10" />
          )}
          <span className="mt-0.5 text-[11px] text-slate-500">{label}</span>
        </div>
      ))}
    </div>
  )
}
