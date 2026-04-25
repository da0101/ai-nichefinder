import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { ValidateFreeResponse } from '@/types/api'

interface Props {
  profile: string
  data: ValidateFreeResponse | null
  running: boolean
  error: string | null
  onRun: (profile: string, keyword: string) => void
}

export function ValidationLabPanel({ profile, data, running, error, onRun }: Props) {
  const [keyword, setKeyword] = useState('')

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Validation Lab</div>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Run phrase validation</h2>
          <p className="mt-2 text-sm text-slate-600">Run `validate-free` for the selected profile from the browser.</p>
        </div>
        <Badge variant="outline">{profile}</Badge>
      </div>

      <div className="flex gap-2">
        <Input
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          placeholder="Enter a phrase to validate"
          className="h-10 flex-1"
        />
        <Button
          type="button"
          disabled={running || !keyword.trim()}
          onClick={() => onRun(profile, keyword)}
          className="h-10 px-4"
        >
          {running ? 'Running...' : 'Run'}
        </Button>
      </div>

      {!data && !error && (
        <div className="mt-4 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-5">
          <div className="text-sm font-medium text-slate-700">Start with one buyer-problem phrase</div>
          <p className="mt-2 text-sm text-slate-500">
            Example: <span className="font-mono text-xs text-slate-700">how to reduce food cost in a restaurant</span>
          </p>
        </div>
      )}

      {error && <p className="mt-3 text-xs text-red-600">{error}</p>}

      {data && (
        <div className="mt-4 space-y-4 text-sm">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <div className="font-medium text-slate-900">{data.keyword}</div>
            <div className="mt-1 text-xs text-slate-500">
              {data.profile} · {data.location} · {data.sources.join(', ')}
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <Section title="Buyer Problems" items={data.buyer_problems.map(item => String(item.problem ?? item.article_angle ?? ''))} />
            <Section title="Shortlist" items={data.shortlist.map(item => `${item.term} (${Math.round(item.score)})`)} />
            <Section title="Keyword Validations" items={data.keyword_validations.map(item => `${item.source}: ${item.query} (${item.score})`)} />
            <Section title="Article Evidence" items={data.article_evidence.map(item => `${item.source}: ${item.query}`)} />
          </div>
        </div>
      )}
    </div>
  )
}

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{title}</div>
        <Badge variant="secondary">{items.length}</Badge>
      </div>
      <div className="max-h-64 space-y-1 overflow-y-auto pr-1">
        {items.length > 0 ? (
          items.map(item => (
            <div key={item} className="rounded border border-slate-200 px-3 py-2 text-slate-700">
              {item}
            </div>
          ))
        ) : (
          <div className="rounded border border-slate-200 px-3 py-2 text-slate-400">No data yet</div>
        )}
      </div>
    </div>
  )
}
