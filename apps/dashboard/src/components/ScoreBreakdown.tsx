import { cn, scoreBarClass } from '@/lib/utils'
import type { ScoreBreakdown as ScoreBreakdownType } from '@/types/api'

interface Props {
  breakdown: ScoreBreakdownType
}

const FACTORS = [
  {
    key: 'volume' as const,
    label: 'Search Demand',
    hint: 'How many people search this',
    weight: '\u00d70.25',
  },
  {
    key: 'difficulty' as const,
    label: 'Ease of Ranking',
    hint: 'Can you realistically rank?',
    weight: '\u00d70.30',
  },
  {
    key: 'trend' as const,
    label: 'Trend Direction',
    hint: 'Rising=100, Stable=50, Declining=0',
    weight: '\u00d70.20',
  },
  {
    key: 'intent' as const,
    label: 'Commercial Value',
    hint: 'Do searchers want to hire/buy?',
    weight: '\u00d70.15',
  },
  {
    key: 'competition' as const,
    label: 'Low Competition',
    hint: 'How easy are results to beat?',
    weight: '\u00d70.10',
  },
]

export function ScoreBreakdown({ breakdown }: Props) {
  return (
    <div className="space-y-3">
      {FACTORS.map(({ key, label, hint, weight }) => {
        const val = breakdown[key] ?? 0
        return (
          <div key={key} className="grid grid-cols-[1fr_auto] items-center gap-3">
            <div>
              <div className="text-[13px] font-medium text-slate-700">{label}</div>
              <div className="mt-0.5 text-[11px] text-slate-400">{hint}</div>
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={cn('h-full rounded-full transition-all', scoreBarClass(val))}
                  style={{ width: `${Math.round(val)}%` }}
                />
              </div>
            </div>
            <div className="text-right">
              <div className="font-mono text-[13px] font-semibold text-slate-700">
                {Math.round(val)}
              </div>
              <div className="text-[10px] text-slate-400">{weight}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
