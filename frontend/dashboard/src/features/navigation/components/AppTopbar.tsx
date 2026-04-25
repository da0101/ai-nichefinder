import { Building2, Check, Menu } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

import { LiveIndicator } from '@/components/LiveIndicator'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useWorkspace } from '@/features/workspace/context/WorkspaceContext'

import { getNavItem } from '../routes'

interface AppTopbarProps {
  onOpenMobileNav: () => void
}

export function AppTopbar({ onOpenMobileNav }: AppTopbarProps) {
  const location = useLocation()
  const route = getNavItem(location.pathname)
  const {
    activeProfile,
    availableProfiles,
    lastUpdated,
    profilesRefreshing,
    refreshWorkspace,
    switchProfile,
  } = useWorkspace()

  const activeSummary =
    availableProfiles.find(profile => profile.slug === activeProfile) ??
    availableProfiles[0]

  return (
    <header className="shrink-0 border-b border-slate-200 bg-white/95 backdrop-blur-sm">
      <div className="flex h-14 w-full items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          {/* Mobile hamburger */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onOpenMobileNav}
            aria-label="Open navigation"
          >
            <Menu className="h-4 w-4" />
          </Button>
          {/* Breadcrumb */}
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-slate-400">
              <span>{route.group}</span>
              <span className="text-slate-300">/</span>
              <span className="text-slate-600">{route.title}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <LiveIndicator lastUpdated={lastUpdated} onRefresh={() => void refreshWorkspace()} />
          <ProfileDropdown
            activeProfile={activeProfile}
            activeSiteName={activeSummary?.site_name ?? 'Default workspace'}
            profiles={availableProfiles}
            refreshing={profilesRefreshing}
            onSwitchProfile={profile => void switchProfile(profile)}
          />
        </div>
      </div>
    </header>
  )
}

function ProfileDropdown({
  activeProfile,
  activeSiteName,
  profiles,
  refreshing,
  onSwitchProfile,
}: {
  activeProfile: string
  activeSiteName: string
  profiles: Array<{
    slug: string
    site_name: string
    keywords: number
    runs: number
  }>
  refreshing: boolean
  onSwitchProfile: (profile: string) => void
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className="h-9 min-w-[11rem] justify-between rounded-lg border-slate-200 bg-white px-3 shadow-sm"
        >
          <span className="flex min-w-0 items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-100 text-slate-600">
              <Building2 className="h-3.5 w-3.5" />
            </span>
            <span className="min-w-0 text-left">
              <span className="block truncate text-sm font-medium text-slate-900">
                {activeSiteName}
              </span>
              <span className="block truncate text-xs text-slate-500">{activeProfile}</span>
            </span>
          </span>
          <Badge variant="outline" className="hidden text-[10px] sm:inline-flex">
            {refreshing ? 'Syncing' : 'Active'}
          </Badge>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[20rem]">
        <DropdownMenuLabel>Switch Business</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {profiles.map(profile => (
          <DropdownMenuItem
            key={profile.slug}
            className="items-start"
            onSelect={event => {
              event.preventDefault()
              onSwitchProfile(profile.slug)
            }}
          >
            <div className="flex min-w-0 flex-1 items-start gap-3">
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                {profile.slug === activeProfile ? (
                  <Check className="h-4 w-4 text-emerald-600" />
                ) : (
                  <Building2 className="h-4 w-4" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <div className="truncate font-medium text-slate-900">{profile.site_name}</div>
                <div className="truncate text-xs text-slate-500">{profile.slug}</div>
                <div className="mt-1 text-xs text-slate-400">
                  {profile.keywords} keywords · {profile.runs} runs
                </div>
              </div>
            </div>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/profiles">Open business settings</Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
