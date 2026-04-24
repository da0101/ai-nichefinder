import { useEffect, useMemo, useState } from 'react'
import { Building2, CheckCircle2, Globe2, Pencil, Plus, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Modal } from '@/components/ui/modal'
import type { ProfileSummary, SiteConfigDto } from '@/types/api'

interface Props {
  profiles: ProfileSummary[]
  activeProfile: string
  loading: boolean
  saving: boolean
  error: string | null
  onDismissError?: () => void
  onSwitchProfile: (profile: string) => void
  onSaveProfile: (profile: string, siteConfig: SiteConfigDto) => void
  onCreateProfile: (input: { slug: string; siteConfig: SiteConfigDto; use?: boolean }) => void
  onDeleteProfile: (profile: string) => void
}

const EMPTY_CONFIG: SiteConfigDto = {
  site_name: '',
  site_url: '',
  site_description: '',
  target_audience: '',
  services: [],
  primary_language: 'en',
  blog_url: '',
  existing_articles: [],
  seed_keywords: [],
  target_persona: '',
  competitors: [],
  geographic_focus: [],
}

export function ProfileConfigPanel({
  profiles,
  activeProfile,
  loading,
  saving,
  error,
  onDismissError,
  onSwitchProfile,
  onSaveProfile,
  onCreateProfile,
  onDeleteProfile,
}: Props) {
  const [editor, setEditor] = useState<{ mode: 'create' | 'edit'; slug: string; draft: SiteConfigDto } | null>(null)
  const [pendingDelete, setPendingDelete] = useState<ProfileSummary | null>(null)
  const sortedProfiles = useMemo(() => [...profiles].sort((a, b) => Number(b.slug === activeProfile) - Number(a.slug === activeProfile)), [profiles, activeProfile])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Business Profiles</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-400">Loading profile registry…</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader className="border-b border-slate-100">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="text-slate-500">Business Profiles</CardTitle>
              <p className="mt-1 text-sm text-slate-600">Manage businesses like web development, restaurants, or gardening as proper app records.</p>
            </div>
            <Button
              type="button"
              className="rounded-xl bg-blue-700 px-4"
              onClick={() => setEditor({ mode: 'create', slug: '', draft: { ...EMPTY_CONFIG } })}
            >
              <Plus className="h-4 w-4" />
              New business
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 pt-4">
          {error && (
            <div className="flex items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <span>
                <span className="font-semibold">Profile action failed:</span> {error}
              </span>
              {onDismissError && (
                <button type="button" className="font-medium text-red-700 underline-offset-2 hover:underline" onClick={onDismissError}>
                  Dismiss
                </button>
              )}
            </div>
          )}

          <div className="grid gap-3 xl:grid-cols-2">
            {sortedProfiles.map(profile => (
              <div key={profile.slug} className={`rounded-2xl border p-4 transition ${profile.slug === activeProfile ? 'border-blue-300 bg-blue-50/60' : 'border-slate-200 bg-white'}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="rounded-xl bg-slate-100 p-2 text-slate-600">
                        <Building2 className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{profile.site_name}</div>
                        <div className="text-xs text-slate-500">{profile.slug}</div>
                      </div>
                    </div>
                    <p className="mt-3 line-clamp-2 text-sm text-slate-600">{profile.site_description || 'No business description yet.'}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {profile.slug === activeProfile && <Badge variant="default">Active</Badge>}
                    {profile.is_default && <Badge variant="outline">Default</Badge>}
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                  <Globe2 className="h-3.5 w-3.5" />
                  <span className="truncate">{profile.site_url || 'No site URL yet'}</span>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
                  <StatPill label="Keywords" value={profile.keywords} />
                  <StatPill label="Runs" value={profile.runs} />
                  <StatPill label="Articles" value={profile.articles} />
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button type="button" variant={profile.slug === activeProfile ? 'outline' : 'default'} className="rounded-xl" onClick={() => onSwitchProfile(profile.slug)}>
                    <CheckCircle2 className="h-4 w-4" />
                    {profile.slug === activeProfile ? 'Selected' : 'Use'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-xl"
                    onClick={() => setEditor({ mode: 'edit', slug: profile.slug, draft: structuredClone(profile.site_config) })}
                  >
                    <Pencil className="h-4 w-4" />
                    Edit
                  </Button>
                  {!profile.is_default && (
                    <Button type="button" variant="outline" className="rounded-xl text-red-600 hover:bg-red-50 hover:text-red-700" onClick={() => setPendingDelete(profile)}>
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <ProfileEditorDialog
        state={editor}
        saving={saving}
        onClose={() => setEditor(null)}
        onSubmit={(slug, draft) => {
          if (editor?.mode === 'create') {
            onCreateProfile({ slug, siteConfig: draft, use: true })
          } else {
            onSaveProfile(slug, draft)
          }
          setEditor(null)
        }}
      />

      <DeleteProfileDialog
        profile={pendingDelete}
        saving={saving}
        onClose={() => setPendingDelete(null)}
        onConfirm={() => {
          if (!pendingDelete) return
          onDeleteProfile(pendingDelete.slug)
          setPendingDelete(null)
        }}
      />
    </>
  )
}

function ProfileEditorDialog({
  state,
  saving,
  onClose,
  onSubmit,
}: {
  state: { mode: 'create' | 'edit'; slug: string; draft: SiteConfigDto } | null
  saving: boolean
  onClose: () => void
  onSubmit: (slug: string, draft: SiteConfigDto) => void
}) {
  const [slug, setSlug] = useState('')
  const [draft, setDraft] = useState<SiteConfigDto>(EMPTY_CONFIG)

  useEffect(() => {
    setSlug(state?.slug ?? '')
    setDraft(state?.draft ?? EMPTY_CONFIG)
  }, [state])

  return (
    <Modal
      open={Boolean(state)}
      onClose={onClose}
      title={state?.mode === 'create' ? 'Create business profile' : `Edit ${state?.slug}`}
      description="Profiles are businesses. Each one keeps its own SEO database, training memory, outputs, and validation history."
    >
      {state && (
        <div className="space-y-4 px-5 py-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Profile slug" value={slug} disabled={state.mode === 'edit'} onChange={setSlug} />
            <Field label="Business name" value={draft.site_name} onChange={value => setDraft({ ...draft, site_name: value })} />
            <Field label="Site URL" value={draft.site_url} onChange={value => setDraft({ ...draft, site_url: value })} />
            <Field label="Primary language" value={draft.primary_language} onChange={value => setDraft({ ...draft, primary_language: value })} />
            <TextArea label="Business description" value={draft.site_description} onChange={value => setDraft({ ...draft, site_description: value })} />
            <TextArea label="Target audience" value={draft.target_audience} onChange={value => setDraft({ ...draft, target_audience: value })} />
            <TextArea label="Services" value={draft.services.join(', ')} onChange={value => setDraft({ ...draft, services: splitList(value) })} />
            <TextArea label="Seed keywords" value={draft.seed_keywords.join(', ')} onChange={value => setDraft({ ...draft, seed_keywords: splitList(value) })} />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
            <Button type="button" variant="outline" className="rounded-xl" onClick={onClose}>Cancel</Button>
            <Button
              type="button"
              className="rounded-xl"
              disabled={saving || !slug.trim() || !draft.site_name.trim()}
              onClick={() => onSubmit(slug.trim(), draft)}
            >
              {saving ? 'Saving…' : state.mode === 'create' ? 'Create business' : 'Save changes'}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}

function DeleteProfileDialog({
  profile,
  saving,
  onClose,
  onConfirm,
}: {
  profile: ProfileSummary | null
  saving: boolean
  onClose: () => void
  onConfirm: () => void
}) {
  return (
    <Modal
      open={Boolean(profile)}
      onClose={onClose}
      title={`Delete ${profile?.site_name ?? 'profile'}?`}
      description="This removes the business record and its isolated SEO storage. Use this only for profiles you no longer need."
      className="max-w-xl"
    >
      <div className="space-y-4 px-5 py-4">
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {profile?.slug} will be removed permanently. The active profile will fall back to `default` if needed.
        </div>
        <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
          <Button type="button" variant="outline" className="rounded-xl" onClick={onClose}>Cancel</Button>
          <Button type="button" className="rounded-xl bg-red-600 hover:bg-red-700" disabled={saving} onClick={onConfirm}>
            {saving ? 'Deleting…' : 'Delete business'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

function StatPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
      <div className="font-mono text-sm font-semibold text-slate-900">{value}</div>
      <div className="mt-1 text-[11px] uppercase tracking-[0.14em] text-slate-500">{label}</div>
    </div>
  )
}

function Field({ label, value, onChange, disabled = false }: { label: string; value: string; onChange: (value: string) => void; disabled?: boolean }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-slate-500">{label}</span>
      <Input value={value} disabled={disabled} onChange={event => onChange(event.target.value)} className="h-10" />
    </label>
  )
}

function TextArea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-slate-500">{label}</span>
      <textarea value={value} onChange={event => onChange(event.target.value)} rows={4} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
    </label>
  )
}

function splitList(value: string): string[] {
  return value.split(',').map(item => item.trim()).filter(Boolean)
}
