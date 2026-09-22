export default function RoutePlaceholderPage({ title, description }) {
  return (
    <section className="route-page">
      <p className="eyebrow">Phase 1 foundation</p>
      <h1>{title}</h1>
      <p className="route-page__description">{description}</p>
      <div className="route-page__note" role="status">This route is wired into the application shell and will be implemented in its feature phase.</div>
    </section>
  );
}
