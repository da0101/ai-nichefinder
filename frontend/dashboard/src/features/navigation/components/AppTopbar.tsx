import { Building2, Check, Menu, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'

import { LiveIndicator } from '@/components/LiveIndicator'
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

interface AppTopbarProps {
  onOpenMobileNav: () => void
}

function toInitials(name: string): string {
  return name
    .split(/[\s\-_]+/)
    .filter(Boolean)
    .map(w => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function AppTopbar({ onOpenMobileNav }: AppTopbarProps) {
  const {
    activeProfile,
    availableProfiles,
    lastUpdated,
    profilesRefreshing,
    refreshWorkspace,
    switchProfile,
  } = useWorkspace()

  const activeSummary =
    availableProfiles.find(p => p.slug === activeProfile) ?? availableProfiles[0]

  const siteName = activeSummary?.site_name ?? activeProfile

  return (
    <header className="shrink-0 bg-[#1a1a1a] text-white">
      <div className="flex h-12 items-center gap-3 pr-4 sm:pr-5">
        {/* Brand — sits in the top-left corner of the dark navbar */}
        <Link
          to="/"
          className="flex h-full shrink-0 items-center gap-2.5 px-4 transition-colors hover:bg-white/[0.04]"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-400/25">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div className="hidden min-w-0 sm:block">
            <div className="truncate text-sm font-semibold tracking-tight text-white">Nichefinder</div>
            <div className="truncate text-[11px] text-white/50">Research control center</div>
          </div>
        </Link>

        {/* Mobile: hamburger only */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-white/70 hover:bg-white/10 hover:text-white lg:hidden"
          onClick={onOpenMobileNav}
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </Button>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right: live dot + workspace avatar */}
        <div className="flex items-center gap-3">
          <LiveIndicator
            lastUpdated={lastUpdated}
            onRefresh={() => void refreshWorkspace()}
          />
          <WorkspaceAvatar
            initials={toInitials(siteName)}
            activeProfile={activeProfile}
            siteName={siteName}
            profiles={availableProfiles}
            refreshing={profilesRefreshing}
            onSwitchProfile={slug => void switchProfile(slug)}
          />
        </div>
      </div>
    </header>
  )
}

function WorkspaceAvatar({
  initials,
  activeProfile,
  siteName,
  profiles,
  onSwitchProfile,
}: {
  initials: string
  activeProfile: string
  siteName: string
  profiles: Array<{ slug: string; site_name: string; keywords: number; runs: number }>
  refreshing: boolean
  onSwitchProfile: (slug: string) => void
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label={`Workspace: ${siteName}`}
          className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-indigo-600 text-[11px] font-bold text-white ring-2 ring-white/20 transition-all hover:ring-indigo-300/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
        >
          {initials}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-60">
        {/* Active workspace info */}
        <div className="px-3 py-2.5">
          <div className="truncate text-sm font-semibold text-slate-900">{siteName}</div>
          <div className="truncate text-xs text-slate-500">{activeProfile} · Local mode</div>
        </div>

        <DropdownMenuSeparator />

        <DropdownMenuLabel className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
          Switch workspace
        </DropdownMenuLabel>

        {profiles.map(profile => {
          const isActive = profile.slug === activeProfile
          return (
            <DropdownMenuItem
              key={profile.slug}
              className="gap-2.5"
              onSelect={e => {
                e.preventDefault()
                onSwitchProfile(profile.slug)
              }}
            >
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                  isActive ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {toInitials(profile.site_name)}
              </span>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm text-slate-900">{profile.site_name}</div>
                <div className="text-xs text-slate-500">
                  {profile.keywords} kw · {profile.runs} runs
                </div>
              </div>
              {isActive && <Check className="h-3.5 w-3.5 shrink-0 text-indigo-600" />}
            </DropdownMenuItem>
          )
        })}

        <DropdownMenuSeparator />

        <DropdownMenuItem asChild>
          <Link to="/profiles" className="flex items-center gap-2">
            <Building2 className="h-3.5 w-3.5" />
            Manage workspaces
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
