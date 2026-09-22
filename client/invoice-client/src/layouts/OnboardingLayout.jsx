import { Outlet } from 'react-router-dom';
import { Brand } from '../components/Header.jsx';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';

export default function OnboardingLayout() {
  return (
    <div className="route-shell route-shell-onboarding">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="onboarding-header"><Brand />{isAuthPreviewEnabled && <span className="dev-preview-badge">Developer preview</span>}</header>
      <main id="main-content" className="route-shell__main">
        <Outlet />
      </main>
    </div>
  );
}
