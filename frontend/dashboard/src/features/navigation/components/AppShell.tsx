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
import { cn } from '@/lib/utils'

import { AppSidebar } from './AppSidebar'
import { AppTopbar } from './AppTopbar'

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <TooltipProvider delayDuration={0}>
      {/*
       * Outer dark stage. GitLab-style: full-width dark navbar across the
       * top, then sidebar + rounded white panel below.
       */}
      <div className="flex h-screen flex-col overflow-hidden bg-[#1a1a1a]">

        {/* ── Top dark navbar (full width) ───────────────────── */}
        <AppTopbar onOpenMobileNav={() => setMobileOpen(true)} />

        {/* ── Sidebar + content row ──────────────────────────── */}
        <div className="flex min-h-0 flex-1 overflow-hidden">

          {/* Desktop sidebar */}
          <aside
            className={cn(
              'hidden shrink-0 flex-col transition-[width] duration-200 lg:flex',
              collapsed ? 'w-14' : 'w-60',
            )}
          >
            <AppSidebar
              collapsed={collapsed}
              onToggleCollapse={() => setCollapsed(v => !v)}
            />
          </aside>

          {/* Mobile nav sheet */}
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetContent side="left" className="w-60 border-r border-white/[0.06] bg-[#1a1a1a] p-0">
              <SheetHeader className="sr-only">
                <SheetTitle>Navigation</SheetTitle>
                <SheetDescription>Browse sections of the Nichefinder dashboard.</SheetDescription>
              </SheetHeader>
              <AppSidebar
                collapsed={false}
                mobile
                onNavigate={() => setMobileOpen(false)}
              />
            </SheetContent>
          </Sheet>

          {/* Floating rounded white content panel */}
          <div className="flex flex-1 flex-col overflow-hidden bg-[#1a1a1a] p-3 pt-0">
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-black/40 bg-white shadow-[0_2px_10px_rgba(0,0,0,0.22)]">
              <main className="flex-1 overflow-y-auto">
                <div className="px-6 py-5 sm:px-8">
                  <Outlet />
                </div>
              </main>
            </div>
          </div>

        </div>
      </div>
    </TooltipProvider>
  )
}
