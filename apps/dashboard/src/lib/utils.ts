import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function scoreColorClass(score: number | null | undefined): string {
  const s = score ?? 0
  if (s >= 70) return 'text-emerald-600'
  if (s >= 50) return 'text-amber-600'
  return 'text-red-600'
}

export function scoreBadgeClass(score: number | null | undefined): string {
  const s = score ?? 0
  if (s >= 70) return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  if (s >= 50) return 'bg-amber-50 text-amber-700 border border-amber-200'
  return 'bg-red-50 text-red-700 border border-red-200'
}

export function scoreBarClass(score: number | null | undefined): string {
  const s = score ?? 0
  if (s >= 70) return 'bg-emerald-500'
  if (s >= 50) return 'bg-amber-500'
  return 'bg-red-500'
}

export function priorityBadgeClass(priority: string | null | undefined): string {
  switch (priority?.toLowerCase()) {
    case 'high': return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
    case 'medium': return 'bg-amber-50 text-amber-700 border border-amber-200'
    default: return 'bg-slate-100 text-slate-500 border border-slate-200'
  }
}

export function timeAgo(date: Date): string {
  const s = Math.floor((Date.now() - date.getTime()) / 1000)
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}
