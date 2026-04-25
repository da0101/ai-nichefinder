import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface WorkspaceOverviewProps {
  activeProfile: string
  databasePath: string
  articlesPath: string
  keywordCount: number
  validationRunning: boolean
}

export function WorkspaceOverview({
  activeProfile,
  databasePath,
  articlesPath,
  keywordCount,
  validationRunning,
}: WorkspaceOverviewProps) {
  return (
    <Card className="border-blue-200 bg-gradient-to-br from-white to-blue-50/50">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-blue-700">Active Workspace</CardTitle>
            <p className="mt-1 text-sm text-slate-700">
              Manage the <span className="font-semibold text-slate-900">{activeProfile}</span> profile, review learned signals, and run new validations from one surface.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{keywordCount} keywords</Badge>
            {validationRunning && <Badge variant="warning">Validation running</Badge>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2">
        <InfoStrip label="Database" value={databasePath} />
        <InfoStrip label="Articles" value={articlesPath} />
      </CardContent>
    </Card>
  )
}

function InfoStrip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white/90 px-4 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</div>
      <div className="mt-2 break-all font-mono text-xs text-slate-700">{value}</div>
    </div>
  )
}
