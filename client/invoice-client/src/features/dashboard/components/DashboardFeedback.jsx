export function DashboardLoading({ label = 'Loading dashboard' }) {
  return (
    <div className="dashboard-feedback dashboard-feedback--loading" role="status" aria-live="polite" aria-label={label}>
      <span className="dashboard-skeleton dashboard-skeleton--wide" />
      <span className="dashboard-skeleton" />
      <span className="dashboard-skeleton dashboard-skeleton--short" />
    </div>
  );
}

export function DashboardError({ onRetry, region }) {
  return (
    <div className="dashboard-feedback dashboard-feedback--error" role="alert">
      <strong>We couldn’t load your {region}.</strong>
      <span>Your documents are safe.</span>
      <button className="button button--secondary" type="button" onClick={onRetry}>Try again</button>
    </div>
  );
}
