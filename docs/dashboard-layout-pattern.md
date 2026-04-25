# GitLab-style Encapsulated App Layout — Porting Guide

A reusable React + Tailwind layout pattern: a full-width dark navbar across the top with logo on the left and status/avatar on the right; below it a dark sidebar on the left and a single rounded white "card" containing the entire scrollable app on the right. The dark stage shows on top (the navbar), left (between sidebar and panel), right, and bottom — visually framing the white app inside one container.

This doc contains everything another agent needs to apply the same look to a different React + Tailwind project. Read it top-to-bottom before touching code.

---

## 1. Visual Anatomy

```
┌─────────────────────────────────────────────────────────────────┐  ← outer dark stage (#1a1a1a)
│ ⛰ Nichefinder              [● Updated 0s ago ↻]   ⏺ DU         │  ← TOP NAVBAR (full width, h-12, dark)
│   Research control center                                       │     • Logo+brand left
├─────────────────────────────────────────────────────────────────┤     • LiveIndicator + Avatar right
│              │                                                  │
│ WORKSPACE    │  ╭─────────── rounded white panel ────────────╮  │
│  Overview    │  │ WORKSPACE                                  │  │  ← SIDEBAR (left, dark, w-60)
│  Keyword Ex. │  │ Keyword Explorer                           │  │     • No logo (lives in navbar)
│              │  │                                            │  │     • Nav items
│ OPERATIONS   │  │   ...content...                            │  │     • Collapse toggle at bottom
│  Research    │  │                                            │  │
│  Reviews     │  │                                            │  │  ← CONTENT PANEL (rounded-xl)
│              │  │                                            │  │     • bg-white, border, shadow
│ ADMIN        │  │                                            │  │     • Holds <main> only
│  Businesses  │  ╰────────────────────────────────────────────╯  │     • Dark frame visible on
│              │                                                  │       left, right, bottom
│  ◀ Collapse  │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
```

Three structural layers (top-down inside the outer stage):

1. **Top dark navbar** (`<AppTopbar>`) — `h-12`, full viewport width, dark background. Brand on left, status+avatar on right.
2. **Sidebar+content row** — flex row that fills the remaining height. Sidebar is `w-60` (or `w-14` collapsed); right column is `flex-1` with dark padding on left/right/bottom (`p-3 pt-0`) wrapping a single rounded-xl white card.
3. **Inside the white card** — only `<main>` with `overflow-y-auto`. Topbar does NOT live here.

---

## 2. Tech Assumptions

- **React 18+** with React Router v6 (`<Outlet>`, `<Link>`, `useLocation`).
- **Tailwind CSS** (any 3.x). All styling uses utility classes — no custom CSS required.
- **Lucide icons** (`lucide-react`).
- **Optional shadcn/ui primitives** for the mobile nav `<Sheet>`, `<Button>`, `<DropdownMenu>`, `<TooltipProvider>`. The pattern works without shadcn — substitute your own primitives.
- **A `cn()` utility** that merges Tailwind class strings (the standard `clsx` + `tailwind-merge` combo).

If the target project doesn't have these, install them first.

---

## 3. The Files You Will Create / Modify

In `src/features/navigation/components/` (or wherever your nav lives):

| File | Role |
|---|---|
| `AppShell.tsx` | Root layout. Owns the dark stage, sidebar collapse state, mobile sheet state. |
| `AppTopbar.tsx` | The full-width top dark navbar. Brand on left, status + avatar on right. |
| `AppSidebar.tsx` | The dark left sidebar. No logo (it's in the navbar). Nav items + collapse toggle. |
| `LiveIndicator.tsx` (optional) | Small "Updated Xs ago • refresh" widget that lives in the navbar. |

The `<Outlet />` from React Router renders inside the white panel.

---

## 4. The Critical Tailwind Classes

These are the lines that make the look work. Don't substitute them blindly — read the "why" column first.

| Class | Where | Why |
|---|---|---|
| `flex h-screen flex-col overflow-hidden bg-[#1a1a1a]` | Root wrapper | Full viewport, vertical stack: navbar on top, row below. `overflow-hidden` so only the inner panel scrolls. |
| `shrink-0 bg-[#1a1a1a] text-white` + `h-12` | `<AppTopbar>` | Fixed-height dark strip at top. Same `#1a1a1a` as outer stage so they read as one continuous dark frame. |
| `flex min-h-0 flex-1 overflow-hidden` | Sidebar+content row | `min-h-0` is **required** so the inner panel can scroll instead of stretching the page. |
| `hidden shrink-0 flex-col lg:flex` + `w-60` / `w-14` | Sidebar `<aside>` | Hides on mobile (use the `<Sheet>`), fixed width on desktop. Toggle between `w-60` and `w-14` for collapse. |
| `flex flex-1 flex-col overflow-hidden bg-[#1a1a1a] p-3 pt-0` | Content column wrapper | `p-3 pt-0` puts dark frame on **left/right/bottom** of the panel; `pt-0` because the navbar is the top frame already. |
| `flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-black/40 bg-white shadow-[0_2px_10px_rgba(0,0,0,0.22)]` | White panel | All four corners rounded. `overflow-hidden` so children don't poke past the radius. `min-h-0` so `<main>` inside can scroll. |
| `flex-1 overflow-y-auto` | `<main>` | The only scrollable region. |
| `px-6 py-5 sm:px-8` | Inner content wrapper | Responsive page padding inside the panel. |

---

## 5. Reference Implementation (Copy-Paste Ready)

### `AppShell.tsx`

```tsx
import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import {
  Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle,
} from '@/components/ui/sheet'
import { TooltipProvider } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

import { AppSidebar } from './AppSidebar'
import { AppTopbar } from './AppTopbar'

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex h-screen flex-col overflow-hidden bg-[#1a1a1a]">

        {/* 1. Top dark navbar — full viewport width */}
        <AppTopbar onOpenMobileNav={() => setMobileOpen(true)} />

        {/* 2. Sidebar + content row */}
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
            <SheetContent side="left" className="w-60 bg-[#1a1a1a] p-0">
              <SheetHeader className="sr-only">
                <SheetTitle>Navigation</SheetTitle>
                <SheetDescription>Browse sections.</SheetDescription>
              </SheetHeader>
              <AppSidebar collapsed={false} mobile onNavigate={() => setMobileOpen(false)} />
            </SheetContent>
          </Sheet>

          {/* 3. Floating rounded white content panel */}
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
```

### `AppTopbar.tsx` (essentials)

```tsx
import { Menu, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
// ...your LiveIndicator and avatar dropdown imports

export function AppTopbar({ onOpenMobileNav }) {
  return (
    <header className="shrink-0 bg-[#1a1a1a] text-white">
      <div className="flex h-12 items-center gap-3 pr-4 sm:pr-5">

        {/* Brand — top-left of the dark navbar */}
        <Link
          to="/"
          className="flex h-full shrink-0 items-center gap-2.5 px-4 transition-colors hover:bg-white/[0.04]"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-400/25">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div className="hidden min-w-0 sm:block">
            <div className="truncate text-sm font-semibold tracking-tight text-white">YourApp</div>
            <div className="truncate text-[11px] text-white/50">Tagline</div>
          </div>
        </Link>

        {/* Mobile: hamburger only */}
        <Button
          variant="ghost" size="icon"
          className="h-8 w-8 text-white/70 hover:bg-white/10 hover:text-white lg:hidden"
          onClick={onOpenMobileNav} aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </Button>

        <div className="flex-1" />

        {/* Right: status + avatar */}
        <div className="flex items-center gap-3">
          <LiveIndicator /* ... */ />
          <AvatarDropdown /* ... */ />
        </div>

      </div>
    </header>
  )
}
```

**Avatar button** — must use light ring on dark surface:

```tsx
className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-indigo-600 text-[11px] font-bold text-white ring-2 ring-white/20 transition-all hover:ring-indigo-300/60"
```

### `AppSidebar.tsx` (essentials)

```tsx
import { ChevronLeft } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'

export function AppSidebar({ collapsed, onToggleCollapse, onNavigate, mobile = false }) {
  return (
    <div className="flex h-full w-full flex-col bg-[#1a1a1a] text-white">
      {/* NO logo block here — the brand lives in the navbar */}

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {/* ... your nav groups + items ... */}
      </nav>

      {/* Collapse toggle — desktop only */}
      {!mobile && onToggleCollapse && (
        <div className="shrink-0 border-t border-white/[0.07] p-2">
          <button
            type="button"
            onClick={onToggleCollapse}
            className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg py-1.5 text-[12px] font-medium text-white/45 transition-colors hover:bg-white/10 hover:text-white/80"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft className={cn('h-4 w-4 shrink-0 transition-transform duration-200', collapsed && 'rotate-180')} />
            {!collapsed && <span>Collapse</span>}
          </button>
        </div>
      )}
    </div>
  )
}
```

### `LiveIndicator.tsx` (dark-surface variant)

```tsx
<div className="flex items-center gap-2 text-xs text-white/60">
  <span className="flex items-center gap-1">
    <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
    {lastUpdated ? `Updated ${timeAgo(lastUpdated)}` : 'Loading…'}
  </span>
  <Button
    variant="ghost" size="icon"
    className="h-6 w-6 cursor-pointer text-white/60 hover:bg-white/10 hover:text-white"
    onClick={onRefresh} aria-label="Refresh"
  >
    <RefreshCw className="h-3 w-3" />
  </Button>
</div>
```

---

## 6. Pitfalls (the bugs I hit while building this)

1. **Topbar inside the white panel.** Original mistake: the topbar was the first child of the rounded panel, so the panel had a flat-top "header" bar instead of the GitLab look. **Fix:** topbar is a sibling ABOVE the sidebar+content row, full viewport width, dark.

2. **Forgetting `min-h-0` on a flex parent.** Without it, `overflow-y-auto` on `<main>` doesn't activate and the whole page scrolls instead of just the panel. Add `min-h-0` to: the sidebar+content row, **and** the inner white panel.

3. **Forgetting `overflow-hidden` on the white panel.** The rounded-xl corners get clipped weirdly — you get sharp edges at the top from inner content rendering past the radius. Both panel and root need `overflow-hidden`.

4. **Padding the top of the content column.** `p-3` on all four sides creates a gap between navbar and panel that looks broken. Use `p-3 pt-0` — the navbar IS the top frame, so no top padding here.

5. **Border on the sidebar's right edge.** Old half-floating layouts used `border-r border-white/[0.06]`. With the new pattern, that competes with the dark gap. Drop the right border; the gap is the separator.

6. **Mismatched stage colors.** The outer wrapper, the topbar, and the content column all use `bg-[#1a1a1a]`. If they differ, you'll see seams where they meet. They MUST be identical.

7. **Light-on-light controls in the navbar.** When you move buttons from a white topbar to a dark one, every `text-slate-400` → `text-white/60`, every `hover:text-indigo-600` → `hover:bg-white/10 hover:text-white`, every `ring-2 ring-white` (avatar) → `ring-2 ring-white/20`. Walk through each control.

8. **Using `rounded-tr-xl rounded-br-xl`.** That's a half-floating variant where the panel meets the sidebar flush on the left. The full-floating GitLab look uses `rounded-xl` (all four corners) and dark padding on the left too.

---

## 7. Variants

- **Tighter / airier frame:** `p-2 pt-0` (8px) or `p-4 pt-0` (16px) on the content column.
- **Sidebar flush with panel** (no left dark gap): swap content column padding to `pl-0 pr-3 pb-3 pt-0` and use `rounded-tr-xl rounded-br-xl` instead of `rounded-xl`. The "half-floating" look — also valid GitLab.
- **Dark mode panel:** swap `bg-white` for your dark surface (e.g. `bg-[#111]`), drop the border to `border-white/10`, keep everything else.
- **Different stage color:** replace every `#1a1a1a` with your chosen neutral (`#0f172a` slate-900, `#18181b` zinc-900, `#111827` gray-900 all work).
- **Brand in sidebar instead of navbar:** revert step 7 of the porting checklist below — keep a logo block at the top of the sidebar and leave the navbar's left side empty. Less GitLab-faithful but valid.

---

## 8. Porting Checklist

For an agent applying this to a fresh project:

- [ ] **Tech check.** Confirm React Router v6, Tailwind 3.x, lucide-react. Add shadcn/ui Sheet/Button/Tooltip/DropdownMenu if you'll use them.
- [ ] **Pick the stage color.** Default is `#1a1a1a`. If the target app has a brand neutral, use that.
- [ ] **Create / replace `AppShell.tsx`** with the structure in §5. Verify the order is: outer dark stage → topbar (sibling) → sidebar+content row → content column with white panel.
- [ ] **Create / replace `AppTopbar.tsx`.** Dark `bg-[#1a1a1a]`. Brand on left wrapped in `<Link to="/">`. Status + avatar on right. Mobile hamburger between brand and spacer.
- [ ] **Create / replace `AppSidebar.tsx`.** Dark `bg-[#1a1a1a]`. **No logo block** at the top — it lives in the navbar. Nav items in the middle. Collapse toggle at the bottom (desktop only), centered, with the word "Collapse" next to the chevron when expanded.
- [ ] **Adapt every navbar control for dark surface.** `text-slate-*` → `text-white/60`, hover ink → `hover:bg-white/10 hover:text-white`, avatar ring → `ring-white/20`.
- [ ] **Route `<Outlet />`** inside the white panel's `<main>`.
- [ ] **Build (`npm run build`).** Check for TS errors from removed props (e.g. `activeProfile`, `keywordCount`, `useWorkspace`).
- [ ] **Hard-refresh in the browser.** Verify:
  - Dark navbar across the full top.
  - Logo in top-left of navbar at the same vertical level as the avatar on the right.
  - Sidebar starts directly with nav items (no redundant logo).
  - White panel rounded on all four corners.
  - Dark frame visible on left (between sidebar and panel), right, and bottom.
  - Only the white panel scrolls; the rest stays fixed.
  - Layout responsive at 375px, 768px, 1024px, 1440px (mobile uses the Sheet).

---

## 9. Where this lives in the source project

For reference when copying:

- `frontend/dashboard/src/features/navigation/components/AppShell.tsx`
- `frontend/dashboard/src/features/navigation/components/AppTopbar.tsx`
- `frontend/dashboard/src/features/navigation/components/AppSidebar.tsx`
- `frontend/dashboard/src/components/LiveIndicator.tsx`
- `frontend/dashboard/src/index.css` (only sets `html, body, #root { height: 100% }` and font-family — nothing layout-specific)

That's the entire pattern. Hand this doc to the next agent and they should be able to replicate it in one pass.
