import type { ProfileSummary } from '@/types/api'

interface Props {
  activeProfile: string
  profiles: ProfileSummary[]
  loading: boolean
  error: string | null
  onChange: (profile: string) => void
  onDismissError?: () => void
}

export function ProfileSwitcher({ activeProfile, profiles, loading, error, onChange, onDismissError }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Active SEO Profile</h2>
          <p className="text-xs text-slate-500">Switch the backend context the dashboard reads from.</p>
        </div>
        {loading && <span className="text-xs text-slate-400">Loading...</span>}
      </div>
      <select
        value={activeProfile}
        onChange={e => onChange(e.target.value)}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none ring-0"
      >
        {profiles.map(profile => (
          <option key={profile.slug} value={profile.slug}>
            {profile.slug} - {profile.site_name}
          </option>
        ))}
      </select>
      {error && (
        <div className="mt-2 flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          <span>{error}</span>
          {onDismissError && (
            <button type="button" className="font-medium text-red-700 underline-offset-2 hover:underline" onClick={onDismissError}>
              Dismiss
            </button>
          )}
        </div>
      )}
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-500">
        {profiles.map(profile => (
          <div
            key={profile.slug}
            className={`rounded-lg border px-3 py-2 ${profile.slug === activeProfile ? 'border-blue-300 bg-blue-50 text-blue-700' : 'border-slate-200 bg-slate-50'}`}
          >
            <div className="font-medium">{profile.slug}</div>
            <div>{profile.keywords} keywords</div>
            <div>{profile.runs} training runs</div>
          </div>
        ))}
      </div>
    </div>
  )
}
