import { ChevronLeft } from 'lucide-react'
import { NavLink, useMatch } from 'react-router-dom'

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

import type { AppNavItem } from '../routes'
import { APP_NAV_ITEMS, NAV_GROUP_ORDER } from '../routes'

interface AppSidebarProps {
  collapsed: boolean
  onToggleCollapse?: () => void
  onNavigate?: () => void
  mobile?: boolean
}

// Separate component so useMatch runs as a hook (not inside .map).
// Radix UI asChild/Slot converts function classNames to source strings via
// Array.join — resolving active state here keeps className a plain string.
function CollapsedNavItem({
  item,
  onNavigate,
}: {
  item: AppNavItem
  onNavigate?: () => void
}) {
  const match = useMatch(item.path)
  const Icon = item.icon
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <NavLink
          to={item.path}
          onClick={onNavigate}
          className={cn(
            'flex items-center justify-center rounded-lg transition-colors mx-auto h-9 w-9',
            match
              ? 'bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-500/20'
              : 'text-white/60 hover:bg-white/10 hover:text-white',
          )}
        >
          <Icon className="h-[18px] w-[18px] shrink-0" />
        </NavLink>
      </TooltipTrigger>
      <TooltipContent side="right">{item.title}</TooltipContent>
    </Tooltip>
  )
}

export function AppSidebar({
  collapsed,
  onToggleCollapse,
  onNavigate,
  mobile = false,
}: AppSidebarProps) {
  return (
    <div className="flex h-full w-full flex-col bg-[#1a1a1a] text-white">

      {/* ── Navigation ──────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {NAV_GROUP_ORDER.map(group => {
          const items = APP_NAV_ITEMS.filter(item => item.group === group)
          return (
            <div key={group} className="mb-5">
              {!collapsed && (
                <div className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-widest text-white/40">
                  {group}
                </div>
              )}
              <div className="space-y-0.5">
                {collapsed
                  ? items.map(item => (
                      <CollapsedNavItem key={item.path} item={item} onNavigate={onNavigate} />
                    ))
                  : items.map(item => {
                      const Icon = item.icon
                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          onClick={onNavigate}
                          className={({ isActive }) =>
                            cn(
                              'flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors',
                              isActive
                                ? 'bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-500/20'
                                : 'text-white/70 hover:bg-white/10 hover:text-white',
                            )
                          }
                        >
                          <Icon className="h-[17px] w-[17px] shrink-0" />
                          <span className="truncate">{item.title}</span>
                        </NavLink>
                      )
                    })}
              </div>
            </div>
          )
        })}
      </nav>

      {/* ── Collapse toggle — desktop only ─────────── */}
      {!mobile && onToggleCollapse && (
        <div className="shrink-0 border-t border-white/[0.07] p-2">
          <button
            type="button"
            onClick={onToggleCollapse}
            className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg py-1.5 text-[12px] font-medium text-white/45 transition-colors hover:bg-white/10 hover:text-white/80"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft
              className={cn('h-4 w-4 shrink-0 transition-transform duration-200', collapsed && 'rotate-180')}
            />
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      )}
    </div>
  )
}
