export default function RetryState({ message, onRetry }) {
  return <div className="retry-state" role="alert"><p>{message}</p><button className="text-button" type="button" onClick={onRetry}>Try again</button></div>;
}
