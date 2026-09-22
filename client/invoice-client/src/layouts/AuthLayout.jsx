import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <div className="route-shell route-shell-auth">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <main id="main-content" className="route-shell__main">
        <Outlet />
      </main>
    </div>
  );
}
