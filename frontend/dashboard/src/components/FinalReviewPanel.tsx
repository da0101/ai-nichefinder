import type { FinalReviewResponse } from '@/types/api'

interface Props {
  data: FinalReviewResponse | null
  loading: boolean
  error: string | null
}

export function FinalReviewPanel({ data, loading, error }: Props) {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-slate-900">Final Review</h2>
        <p className="mt-2 text-sm text-slate-400">Loading profile comparison...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4">
        <h2 className="text-sm font-semibold text-red-800">Final Review</h2>
        <p className="mt-2 text-sm text-red-600">{error}</p>
      </div>
    )
  }

  if (!data || data.summary.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-slate-900">Final Review</h2>
        <p className="mt-2 text-sm text-slate-500">
          No profile comparison available yet. Create another profile and run validations to compare learned signals across businesses.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-slate-900">Final Review</h2>
        <p className="text-xs text-slate-500">Cross-profile training summary.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="pb-2 pr-4">Profile</th>
              <th className="pb-2 pr-4">Runs</th>
              <th className="pb-2 pr-4">Noise</th>
              <th className="pb-2 pr-4">Validity</th>
              <th className="pb-2">Legitimacy</th>
            </tr>
          </thead>
          <tbody>
            {data.summary.map(row => (
              <tr key={row.slug} className="border-t border-slate-100 text-slate-700">
                <td className="py-2 pr-4 font-medium">{row.slug}</td>
                <td className="py-2 pr-4">{row.runs}</td>
                <td className="py-2 pr-4">{row.approved_noise}</td>
                <td className="py-2 pr-4">{row.approved_validity}</td>
                <td className="py-2">{row.approved_legitimacy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-2">
        <SharedList title="Shared valid keywords" values={data.shared_valid_keywords} />
        <SharedList title="Shared trusted domains" values={data.shared_trusted_domains} />
      </div>
    </div>
  )
}

function SharedList({ title, values }: { title: string; values: string[] }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</div>
      <div className="mt-2 text-sm text-slate-700">
        {values.length > 0 ? values.join(', ') : 'None yet'}
      </div>
    </div>
  )
}
