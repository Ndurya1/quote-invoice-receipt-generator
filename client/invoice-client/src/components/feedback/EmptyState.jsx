export default function EmptyState({ title, description, action }) {
  return <div className="empty-state"><h2>{title}</h2><p>{description}</p>{action}</div>;
}
