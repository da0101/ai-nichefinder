import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useWorkspace } from '@/features/workspace/context/WorkspaceContext'
import { cn } from '@/lib/utils'

import { AppSidebar } from './AppSidebar'
import { AppTopbar } from './AppTopbar'

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { activeProfile, sortedKeywords } = useWorkspace()

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex h-screen overflow-hidden bg-slate-50 text-slate-900">
        {/* Desktop sidebar — flex child, no fixed positioning */}
        <aside
          className={cn(
            'hidden shrink-0 flex-col border-r border-slate-800 bg-slate-950 transition-[width] duration-200 lg:flex',
            collapsed ? 'w-14' : 'w-60',
          )}
        >
          <AppSidebar
            collapsed={collapsed}
            activeProfile={activeProfile}
            keywordCount={sortedKeywords.length}
            onToggleCollapse={() => setCollapsed(v => !v)}
          />
        </aside>

        {/* Mobile nav sheet */}
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetContent
            side="left"
            className="w-60 border-r border-slate-800 bg-slate-950 p-0"
          >
            <SheetHeader className="sr-only">
              <SheetTitle>Navigation</SheetTitle>
              <SheetDescription>Browse sections of the Nichefinder dashboard.</SheetDescription>
            </SheetHeader>
            <AppSidebar
              collapsed={false}
              mobile
              activeProfile={activeProfile}
              keywordCount={sortedKeywords.length}
              onNavigate={() => setMobileOpen(false)}
            />
          </SheetContent>
        </Sheet>

        {/* Main content column */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <AppTopbar onOpenMobileNav={() => setMobileOpen(true)} />
          <main className="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
            <div className="w-full">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </TooltipProvider>
  )
}
