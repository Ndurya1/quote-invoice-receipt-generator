export function ClientsLoading() {
  return (
    <div className="client-feedback" role="status" aria-live="polite">
      <span className="client-skeleton client-skeleton--wide" />
      <span className="client-skeleton" />
      <span className="client-skeleton client-skeleton--short" />
    </div>
  );
}

export function ClientsError({ message, onRetry }) {
  return (
    <div className="client-feedback client-feedback--error" role="alert">
      <strong>{message || 'We couldn’t load your clients.'}</strong>
      <span>Your client records are safe.</span>
      <button className="button button--secondary" type="button" onClick={onRetry}>Try again</button>
    </div>
  );
}
