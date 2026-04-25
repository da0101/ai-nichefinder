import type { LucideIcon } from 'lucide-react'
import {
  Building2,
  FlaskConical,
  LayoutDashboard,
  SearchCode,
  ShieldCheck,
} from 'lucide-react'

export type NavGroup = 'Workspace' | 'Operations' | 'Administration'

export interface AppNavItem {
  path: string
  title: string
  description: string
  group: NavGroup
  icon: LucideIcon
}

export const APP_NAV_ITEMS: AppNavItem[] = [
  {
    path: '/overview',
    title: 'Overview',
    description: 'Portfolio metrics, top opportunities, and workspace health.',
    group: 'Workspace',
    icon: LayoutDashboard,
  },
  {
    path: '/explorer',
    title: 'Keyword Explorer',
    description: 'Prioritized keyword queue, SERP drill-down, and brief context.',
    group: 'Workspace',
    icon: SearchCode,
  },
  {
    path: '/research',
    title: 'Research Ops',
    description: 'Run validation, review evidence, and train the niche model.',
    group: 'Operations',
    icon: FlaskConical,
  },
  {
    path: '/reviews',
    title: 'Reviews',
    description: 'Cross-profile training review and approval surfaces.',
    group: 'Operations',
    icon: ShieldCheck,
  },
  {
    path: '/profiles',
    title: 'Businesses',
    description: 'Manage isolated business profiles, settings, and storage.',
    group: 'Administration',
    icon: Building2,
  },
]

export const NAV_GROUP_ORDER: NavGroup[] = ['Workspace', 'Operations', 'Administration']

export function getNavItem(pathname: string): AppNavItem {
  return APP_NAV_ITEMS.find(item => item.path === pathname) ?? APP_NAV_ITEMS[0]
}
