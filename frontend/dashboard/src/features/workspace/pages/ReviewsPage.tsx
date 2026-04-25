import { Badge } from '@/components/ui/badge'
import { FinalReviewPanel } from '@/components/FinalReviewPanel'
import { TrainingReviewPanel } from '@/components/TrainingReviewPanel'
import { useWorkspace } from '@/features/workspace/context/WorkspaceContext'
import { PageHeader } from '../components/PageHeader'

export function ReviewsPage() {
  const {
    activeProfile,
    trainingReview,
    trainingLoading,
    trainingError,
    approvingTraining,
    approveCandidate,
    finalReview,
    finalReviewLoading,
    finalReviewError,
  } = useWorkspace()

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Operations"
        title="Reviews"
        description="Compare training signals, approve repeated evidence, and keep the active workspace ready for the next validation cycle."
        meta={<Badge variant="outline">{activeProfile}</Badge>}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <FinalReviewPanel
          data={finalReview}
          loading={finalReviewLoading}
          error={finalReviewError}
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
