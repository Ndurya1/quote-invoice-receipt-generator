import { useState } from 'react';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/useAuth.js';
import Button from '../../components/ui/Button.jsx';
import { routePaths } from '../../utils/routePaths.js';

function displayValue(value) {
  return value || 'Not provided';
}

export default function AccountSettingsPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      navigate(routePaths.login, { replace: true });
    } finally {
      setLoggingOut(false);
    }
  }

  return <section className="settings-page" aria-labelledby="account-settings-title">
    <header className="page-header settings-header"><div><h1 id="account-settings-title">Account</h1><p className="page-header__description">Review the account currently connected to this workspace.</p></div></header>
    <div className="settings-stack">
      <section className="settings-card" aria-labelledby="account-details-title"><h2 id="account-details-title">Account details</h2><dl className="settings-details"><div><dt>Name</dt><dd>{displayValue(user?.name)}</dd></div><div><dt>Email</dt><dd>{displayValue(user?.email)}</dd></div><div><dt>Phone</dt><dd>{displayValue(user?.phone)}</dd></div></dl></section>
      <section className="settings-card settings-card--quiet" aria-labelledby="account-access-title"><h2 id="account-access-title">Account access</h2><p>Account name, email, and password changes are not available yet. Your session can be ended from here at any time.</p><Button variant="danger-ghost" type="button" loading={loggingOut} loadingLabel="Logging out..." onClick={handleLogout}><LogOut size={16} aria-hidden="true" /> Log out</Button></section>
    </div>
  </section>;
}
