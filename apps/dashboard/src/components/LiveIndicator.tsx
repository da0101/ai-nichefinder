import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { timeAgo } from '@/lib/utils'

interface Props {
  lastUpdated: Date | null
  onRefresh: () => void
}

export function LiveIndicator({ lastUpdated, onRefresh }: Props) {
  const [, setTick] = useState(0)

  // Re-render every 15s so the "X ago" text stays fresh
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 15_000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="flex items-center gap-2 text-xs text-slate-400">
      <span className="flex items-center gap-1">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
        {lastUpdated ? `Updated ${timeAgo(lastUpdated)}` : 'Loading\u2026'}
      </span>
      <Button
        variant="ghost"
        size="icon"
        onClick={onRefresh}
        title="Refresh now"
        aria-label="Refresh dashboard"
        className="h-6 w-6 text-slate-400 hover:text-blue-600"
      >
        <RefreshCw className="h-3 w-3" />
      </Button>
    </div>
  )
}
