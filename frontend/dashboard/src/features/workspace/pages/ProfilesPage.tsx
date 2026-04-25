import { Building2, Database, FolderTree } from 'lucide-react'

import { ProfileConfigPanel } from '@/components/ProfileConfigPanel'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useWorkspace } from '@/features/workspace/context/WorkspaceContext'
import { PageHeader } from '../components/PageHeader'

export function ProfilesPage() {
  const {
    activeProfile,
    availableProfiles,
    dashboardData,
    profilesLoading,
    profilesRefreshing,
    profilesError,
    clearProfilesError,
    switchProfile,
    createProfile,
    updateProfile,
    deleteProfile,
  } = useWorkspace()

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Administration"
        title="Businesses"
        description="Keep each business isolated so research, training memory, and outputs never bleed across niches."
        meta={
          <>
            <Badge variant="outline">{availableProfiles.length} profiles</Badge>
            <Badge variant="secondary">{activeProfile}</Badge>
          </>
        }
      />

      <section className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2 text-slate-500">
              <Building2 className="h-4 w-4" />
              <CardTitle>Business Registry</CardTitle>
            </div>
            <p className="mt-2 text-sm text-slate-600">
              Each business owns its own database, cache, outputs, and training memory.
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            <RegistryStat label="Businesses" value={availableProfiles.length} icon={Building2} />
            <RegistryStat label="Tracked keywords" value={dashboardData?.summary.total_keywords ?? 0} icon={Database} />
            <RegistryStat label="Article outputs" value={dashboardData?.summary.articles ?? 0} icon={FolderTree} />
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              Active business: <span className="font-medium text-slate-900">{activeProfile}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>Business Boundaries</CardTitle>
                <p className="mt-2 text-sm text-slate-600">
                  Keep restaurant, SaaS, and consulting research isolated so training signals stay trustworthy.
                </p>
              </div>
              <div className="flex gap-2">
                <Badge variant="outline">{availableProfiles.length} profiles</Badge>
                <Badge variant="secondary">SQLite isolated</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <BoundaryItem title="Database" value={dashboardData?.paths.database ?? 'No database path available'} />
            <BoundaryItem title="Articles" value={dashboardData?.paths.articles_dir ?? 'No articles path available'} />
            <BoundaryItem title="Workspace" value={activeProfile} />
          </CardContent>
        </Card>
      </section>

      <ProfileConfigPanel
        profiles={availableProfiles}
        activeProfile={activeProfile}
        loading={profilesLoading}
        saving={profilesRefreshing}
        error={profilesError}
        onDismissError={clearProfilesError}
        onSwitchProfile={profile => void switchProfile(profile)}
        onSaveProfile={(profile, siteConfig) => void updateProfile(profile, siteConfig)}
        onCreateProfile={input => void createProfile(input)}
        onDeleteProfile={profile => void deleteProfile(profile)}
      />
    </div>
  )
}

function RegistryStat({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: number
  icon: typeof Building2
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center gap-2 text-slate-500">
        <Icon className="h-4 w-4" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">{label}</span>
      </div>
      <div className="mt-3 font-mono text-2xl font-semibold text-slate-900">{value}</div>
    </div>
  )
}

function BoundaryItem({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{title}</div>
      <div className="mt-2 break-all text-sm text-slate-700">{value}</div>
    </div>
  )
}
