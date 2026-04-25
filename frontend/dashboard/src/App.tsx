import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/features/navigation/components/AppShell'
import { WorkspaceProvider } from '@/features/workspace/context/WorkspaceContext'
import { KeywordExplorerPage } from '@/features/workspace/pages/KeywordExplorerPage'
import { OverviewPage } from '@/features/workspace/pages/OverviewPage'
import { ProfilesPage } from '@/features/workspace/pages/ProfilesPage'
import { ResearchOpsPage } from '@/features/workspace/pages/ResearchOpsPage'
import { ReviewsPage } from '@/features/workspace/pages/ReviewsPage'

export default function App() {
  return (
    <WorkspaceProvider>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<OverviewPage />} />
          <Route path="/research" element={<ResearchOpsPage />} />
          <Route path="/explorer" element={<KeywordExplorerPage />} />
          <Route path="/reviews" element={<ReviewsPage />} />
          <Route path="/profiles" element={<ProfilesPage />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Route>
      </Routes>
    </WorkspaceProvider>
  )
}
