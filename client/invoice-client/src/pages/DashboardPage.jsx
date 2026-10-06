import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/useAuth.js';
import { routePaths } from '../utils/routePaths.js';
import CreateDocumentMenu from '../features/dashboard/components/CreateDocumentMenu.jsx';
import { DashboardError, DashboardLoading } from '../features/dashboard/components/DashboardFeedback.jsx';
import DashboardAttention from '../features/dashboard/components/DashboardAttention.jsx';
import OverviewBand from '../features/dashboard/components/OverviewBand.jsx';
import QuickActions from '../features/dashboard/components/QuickActions.jsx';
import RecentDocumentsSection from '../features/dashboard/components/RecentDocumentsSection.jsx';
import { useDashboardSummary } from '../features/dashboard/useDashboardSummary.js';

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function DashboardPage() {
  const { user, businessProfile } = useAuth();
  const { data, status, retry } = useDashboardSummary();
  const displayName = businessProfile?.business_name || user?.name || 'there';
  const dashboardData = data || { quotes: { total: 0 }, invoices: { total: 0, paid: 0, overdue: 0 }, receipts: { total: 0 }, recentDocuments: [] };
  const profileNotice = !businessProfile;
  const pageDescription = useMemo(() => `${greeting()}, ${displayName}.`, [displayName]);

  return (
    <section className="dashboard-page" aria-labelledby="dashboard-title">
      <header className="dashboard-header page-header">
        <div>
          <p className="eyebrow">Workspace overview</p>
          <h1 id="dashboard-title">Dashboard</h1>
          <p className="page-header__description dashboard-greeting">{pageDescription}</p>
        </div>
        <div className="dashboard-header__actions page-header__actions">
          <CreateDocumentMenu />
        </div>
      </header>

      <QuickActions />

      {profileNotice && (
        <div className="dashboard-notice dashboard-notice--setup" role="status">
          <div><strong>Add your business details before creating a document.</strong><span>Your profile will be reused across future documents.</span></div>
          <Link className="text-link" to={routePaths.onboardingBusiness}>Complete setup</Link>
        </div>
      )}

      <div className="dashboard-region">
        {status === 'loading' && <DashboardLoading label="Loading document overview" />}
        {status === 'error' && <DashboardError region="document overview" onRetry={retry} />}
        {status === 'success' && <OverviewBand summary={data} />}
      </div>

      <div className={`dashboard-workspace${!profileNotice && (dashboardData.invoices.overdue > 0 || dashboardData.quotes.sent > 0) ? ' dashboard-workspace--with-attention' : ''}`}>
        <div className="dashboard-region">
          {status === 'loading' && <DashboardLoading label="Loading recent documents" />}
          {status === 'error' && <DashboardError region="recent documents" onRetry={retry} />}
          {status === 'success' && <RecentDocumentsSection summary={dashboardData} />}
        </div>
        {!profileNotice && status === 'success' && <DashboardAttention summary={dashboardData} />}
      </div>
    </section>
  );
}
