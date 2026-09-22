import OnboardingProgress from './OnboardingProgress.jsx';
import BusinessDocumentPreview from './BusinessDocumentPreview.jsx';

export default function OnboardingShell({ step, title, description, draft, children }) {
  return <section className="onboarding-page" aria-labelledby="onboarding-title">
    <header className="onboarding-heading">
      <OnboardingProgress step={step} />
      <h1 id="onboarding-title">{title}</h1>
      <p>{description}</p>
    </header>
    <div className="onboarding-grid">
      <div className="onboarding-form-column">{children}</div>
      <aside className="onboarding-preview-column" aria-label="Document preview">
        <BusinessDocumentPreview draft={draft} />
      </aside>
    </div>
  </section>;
}
