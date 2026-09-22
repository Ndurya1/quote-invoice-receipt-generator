import { Outlet } from 'react-router-dom';
import { Brand } from '../components/Header.jsx';

export default function AuthLayout() {
  return (
    <div className="route-shell route-shell-auth">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="auth-header"><Brand /></header>
      <main id="main-content" className="route-shell__main">
        <Outlet />
      </main>
      <p className="auth-footer">Professional documents for people doing real work.</p>
    </div>
  );
}
