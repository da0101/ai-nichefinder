import { useState } from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { cn, scoreBadgeClass } from '@/lib/utils'
import type { KeywordSummary } from '@/types/api'

interface Props {
  keywords: KeywordSummary[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function KeywordList({ keywords, selectedId, onSelect }: Props) {
  const [query, setQuery] = useState('')

  const filtered = query
    ? keywords.filter(k => k.term.toLowerCase().includes(query.toLowerCase()))
    : keywords

  return (
    <div className="flex h-full flex-col">
      {/* Search */}
      <div className="border-b border-slate-200 p-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <Input
            className="pl-8 text-sm"
            placeholder="Filter keywords\u2026"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Header */}
      <div className="border-b border-slate-200 px-4 py-2 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        {filtered.length} keyword{filtered.length !== 1 ? 's' : ''}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-slate-400">
            {query ? 'No matches' : 'No keywords yet \u2014 run seo research first'}
          </p>
        ) : (
          filtered.map(kw => (
            <button
              key={kw.id}
              onClick={() => onSelect(kw.id)}
              aria-current={selectedId === kw.id ? 'page' : undefined}
              className={cn(
                'w-full cursor-pointer border-b border-slate-100 px-4 py-3 text-left transition-colors',
                'hover:bg-indigo-50',
                selectedId === kw.id
                  ? 'border-l-2 border-l-indigo-600 bg-indigo-50'
                  : 'border-l-2 border-l-transparent'
              )}
            >
              <div className="truncate text-[13px] font-semibold text-slate-800" title={kw.term}>
                {kw.term}
              </div>
              <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                <span
                  className={cn(
                    'inline-flex items-center rounded px-1.5 py-0.5 font-mono text-[11px] font-semibold',
                    scoreBadgeClass(kw.score)
                  )}
                >
                  {Math.round(kw.score ?? 0)}
                </span>
                {kw.intent && (
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
                    {kw.intent}
                  </span>
                )}
                {kw.trend && (
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
                    {kw.trend}
                  </span>
                )}
                {kw.has_brief && (
                  <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600">
                    brief
                  </span>
                )}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
