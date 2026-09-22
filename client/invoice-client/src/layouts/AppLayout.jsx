import { NavLink, Outlet } from 'react-router-dom';
import { routePaths } from '../utils/routePaths';

const navigation = [
  { label: 'Dashboard', to: routePaths.dashboard, end: true },
  { label: 'Documents', to: routePaths.documents },
  { label: 'Clients', to: routePaths.clients },
];

export default function AppLayout() {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside className="app-sidebar" aria-label="Primary navigation">
        <NavLink className="app-brand" to={routePaths.dashboard}>DocuFlow</NavLink>
        <nav className="app-nav">
          {navigation.map((item) => (
            <NavLink key={item.to} end={item.end} to={item.to} className={({ isActive }) => isActive ? 'app-nav__link is-active' : 'app-nav__link'}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <nav className="app-nav app-nav--secondary" aria-label="Secondary navigation">
          <NavLink to={routePaths.businessSettings} className={({ isActive }) => isActive ? 'app-nav__link is-active' : 'app-nav__link'}>Business settings</NavLink>
          <NavLink to={routePaths.accountSettings} className={({ isActive }) => isActive ? 'app-nav__link is-active' : 'app-nav__link'}>Account</NavLink>
        </nav>
      </aside>
      <header className="app-mobile-header">
        <NavLink className="app-brand" to={routePaths.dashboard}>DocuFlow</NavLink>
      </header>
      <main id="main-content" className="app-main"><Outlet /></main>
      <nav className="app-mobile-nav" aria-label="Mobile navigation">
        <NavLink end to={routePaths.dashboard} className={({ isActive }) => isActive ? 'app-mobile-nav__link is-active' : 'app-mobile-nav__link'}>Home</NavLink>
        <NavLink to={routePaths.documents} className={({ isActive }) => isActive ? 'app-mobile-nav__link is-active' : 'app-mobile-nav__link'}>Documents</NavLink>
        <NavLink to={routePaths.clients} className={({ isActive }) => isActive ? 'app-mobile-nav__link is-active' : 'app-mobile-nav__link'}>Clients</NavLink>
        <NavLink to={routePaths.accountSettings} className={({ isActive }) => isActive ? 'app-mobile-nav__link is-active' : 'app-mobile-nav__link'}>More</NavLink>
      </nav>
    </div>
  );
}
