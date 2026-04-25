import { ChevronLeft, Sparkles, TrendingUp } from 'lucide-react'
import { NavLink, useMatch } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
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
  activeProfile: string
  keywordCount: number
  onToggleCollapse?: () => void
  onNavigate?: () => void
  mobile?: boolean
}

// Separate component so useMatch can be called as a hook (not inside .map)
// Radix UI asChild/Slot converts function classNames to their source string via
// Array.join — this resolves active state to a plain string before Slot sees it.
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
            'flex items-center rounded-lg text-[13px] font-medium transition-colors mx-auto h-9 w-9 justify-center',
            match
              ? 'bg-slate-800 text-white ring-1 ring-inset ring-slate-700'
              : 'text-slate-400 hover:bg-slate-900 hover:text-white',
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
  activeProfile,
  keywordCount,
  onToggleCollapse,
  onNavigate,
  mobile = false,
}: AppSidebarProps) {
  return (
    <div className="flex h-full w-full flex-col bg-slate-950 text-slate-100">
      {/* Logo / brand */}
      <div
        className={cn(
          'flex h-14 shrink-0 items-center border-b border-slate-800',
          collapsed ? 'justify-center px-2' : 'gap-2.5 px-4',
        )}
      >
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-400/20">
          <TrendingUp className="h-4 w-4" />
        </div>
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">Nichefinder</div>
            <div className="truncate text-xs text-slate-400">Research control center</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {NAV_GROUP_ORDER.map(group => {
          const items = APP_NAV_ITEMS.filter(item => item.group === group)
          return (
            <div key={group} className="mb-4">
              {!collapsed && (
                <div className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
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
                              'flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors',
                              isActive
                                ? 'bg-slate-800 text-white ring-1 ring-inset ring-slate-700'
                                : 'text-slate-400 hover:bg-slate-900 hover:text-white',
                            )
                          }
                        >
                          <Icon className="h-[18px] w-[18px] shrink-0" />
                          <span className="truncate">{item.title}</span>
                        </NavLink>
                      )
                    })}
              </div>
            </div>
          )
        })}
      </nav>

      {/* Active profile chip */}
      <div className={cn('border-t border-slate-800', collapsed ? 'p-2' : 'p-3')}>
        <div
          className={cn(
            'rounded-lg border border-slate-800 bg-slate-900/70',
            collapsed ? 'flex flex-col items-center py-3' : 'p-3',
          )}
        >
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex h-9 w-9 cursor-default items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-300">
                  <Sparkles className="h-4 w-4" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="right">{activeProfile}</TooltipContent>
            </Tooltip>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-300">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{activeProfile}</div>
                  <div className="truncate text-xs text-slate-400">{keywordCount} tracked keywords</div>
                </div>
              </div>
              <Badge className="mt-3 w-full justify-center bg-slate-800 text-slate-200">
                Local mode
              </Badge>
            </>
          )}
        </div>
      </div>

      {/* Collapse toggle (desktop only) */}
      {!mobile && onToggleCollapse && (
        <div className="shrink-0 border-t border-slate-800 p-2">
          <button
            type="button"
            onClick={onToggleCollapse}
            className="flex w-full items-center justify-center rounded-lg py-1.5 text-slate-500 transition-colors hover:bg-slate-800 hover:text-slate-200"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft
              className={cn(
                'h-4 w-4 transition-transform duration-200',
                collapsed && 'rotate-180',
              )}
            />
          </button>
        </div>
      )}
    </div>
  )
}
