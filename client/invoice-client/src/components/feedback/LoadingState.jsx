export default function LoadingState({ label = 'Loading…' }) {
  return <div className="loading-state" role="status" aria-live="polite"><span className="loading-state__line" /><span className="loading-state__line loading-state__line--short" /><span className="sr-only">{label}</span></div>;
}
