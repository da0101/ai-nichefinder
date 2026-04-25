import type { TrainingCandidate, TrainingReviewResponse } from '@/types/api'

interface Props {
  data: TrainingReviewResponse | null
  loading: boolean
  error: string | null
  approving: boolean
  onApprove: (candidate: TrainingCandidate) => void
}

const LABEL_ORDER: Array<'validity' | 'legitimacy' | 'noise'> = ['validity', 'legitimacy', 'noise']

export function TrainingReviewPanel({ data, loading, error, approving, onApprove }: Props) {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-slate-900">Training Review</h2>
        <p className="mt-2 text-sm text-slate-400">Loading training candidates...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4">
        <h2 className="text-sm font-semibold text-red-800">Training Review</h2>
        <p className="mt-2 text-sm text-red-600">{error}</p>
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Training Review</h2>
          <p className="text-xs text-slate-500">
            {data.profile.site_name} · {data.profile.site_url}
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <SummaryBadge label="Noise" value={data.profile.approved_noise} tone="red" />
          <SummaryBadge label="Validity" value={data.profile.approved_validity} tone="green" />
          <SummaryBadge label="Legitimacy" value={data.profile.approved_legitimacy} tone="blue" />
        </div>
      </div>

      {data.candidates.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center">
          <div className="text-sm font-medium text-slate-700">No training candidates yet</div>
          <p className="mt-2 text-sm text-slate-500">
            Run a few validations in the browser, then return here to approve repeated noise, valid phrases, and trusted domains.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {LABEL_ORDER.map(label => {
            const scoped = data.candidates.filter(candidate => candidate.label === label)
            if (scoped.length === 0) return null
            return (
              <div key={label}>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</h3>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">{scoped.length}</span>
                </div>
                <div className="space-y-2">
                  {scoped.map(candidate => (
                    <CandidateRow
                      key={`${candidate.label}:${candidate.scope}:${candidate.value}`}
                      candidate={candidate}
                      approving={approving}
                      onApprove={onApprove}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function CandidateRow({
  candidate,
  approving,
  onApprove,
}: {
  candidate: TrainingCandidate
  approving: boolean
  onApprove: (candidate: TrainingCandidate) => void
}) {
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-medium text-slate-900">{candidate.value}</div>
          <div className="mt-1 text-xs text-slate-500">
            {candidate.scope.replace(/_/g, ' ')} · {candidate.support_runs} runs · {candidate.support_count} hits
          </div>
          {candidate.examples.length > 0 && (
            <div className="mt-2 text-xs text-slate-400">
              Examples: {candidate.examples.join(' ; ')}
            </div>
          )}
        </div>
        <button
          type="button"
          disabled={approving}
          onClick={() => onApprove(candidate)}
          className="rounded-md border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 transition hover:bg-blue-100 disabled:opacity-50"
        >
          Approve
        </button>
      </div>
    </div>
  )
}

function SummaryBadge({ label, value, tone }: { label: string; value: number; tone: 'red' | 'green' | 'blue' }) {
  const toneClass =
    tone === 'red'
      ? 'border-red-200 bg-red-50 text-red-700'
      : tone === 'green'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
      : 'border-blue-200 bg-blue-50 text-blue-700'
  return (
    <div className={`rounded-lg border px-2 py-1.5 ${toneClass}`}>
      <div className="font-mono text-sm font-semibold">{value}</div>
      <div>{label}</div>
    </div>
  )
}
