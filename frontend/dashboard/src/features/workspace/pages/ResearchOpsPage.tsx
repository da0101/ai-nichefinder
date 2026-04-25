import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrainingReviewPanel } from '@/components/TrainingReviewPanel'
import { ValidationLabPanel } from '@/components/ValidationLabPanel'
import { useWorkspace } from '@/features/workspace/context/WorkspaceContext'
import { PageHeader } from '../components/PageHeader'

export function ResearchOpsPage() {
  const {
    activeProfile,
    trainingReview,
    trainingLoading,
    trainingError,
    approvingTraining,
    approveCandidate,
    validationRun,
    validationRunning,
    validationError,
    runValidation,
  } = useWorkspace()

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Operations"
        title="Research Ops"
        description="Run validation, review repeated evidence, and train the niche model from one operational surface."
        meta={
          <>
            <Badge variant="outline">{activeProfile}</Badge>
            {validationRunning && <Badge variant="warning">Validation running</Badge>}
          </>
        }
      />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Research Summary</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <ResearchStat
            label="Candidate approvals"
            value={trainingReview?.candidates.length ?? 0}
          />
          <ResearchStat
            label="Noise approved"
            value={trainingReview?.profile.approved_noise ?? 0}
          />
          <ResearchStat
            label="Trusted signals"
            value={trainingReview?.profile.approved_legitimacy ?? 0}
          />
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <ValidationLabPanel
          profile={activeProfile}
          data={validationRun}
          running={validationRunning}
          error={validationError}
          onRun={(profile, keyword) => void runValidation(profile, keyword)}
        />
        <TrainingReviewPanel
          data={trainingReview}
          loading={trainingLoading}
          error={trainingError}
          approving={approvingTraining}
          onApprove={candidate => void approveCandidate(candidate)}
        />
      </div>
    </div>
  )
}

function ResearchStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-3 font-mono text-2xl font-semibold text-slate-900">{value}</div>
    </div>
  )
}
