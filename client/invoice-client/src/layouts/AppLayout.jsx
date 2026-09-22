import { NavLink, Outlet, useLocation } from 'react-router-dom';
import AccountMenu from '../components/navigation/AccountMenu.jsx';
import ApplicationBrand from '../components/navigation/ApplicationBrand.jsx';
import RouteFocusManager from '../components/navigation/RouteFocusManager.jsx';
import { mobileNavigation, primaryNavigation, secondaryNavigation, isNavigationItemActive } from '../navigation/navigation.js';

function NavigationLink({ item, mobile = false, pathname }) {
  const active = isNavigationItemActive(item, pathname);
  const className = mobile ? 'app-mobile-nav__link' : 'app-nav__link';
  return <NavLink end={item.end} to={item.to} className={`${className}${active ? ' is-active' : ''}`} aria-current={active ? 'page' : undefined}>
    {item.label}
  </NavLink>;
}

export default function AppLayout() {
  const { pathname } = useLocation();
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="app-sidebar" aria-label="Primary navigation">
      <ApplicationBrand />
      <nav className="app-nav" aria-label="Primary navigation">
        {primaryNavigation.map((item) => <NavigationLink key={item.to} item={item} pathname={pathname} />)}
      </nav>
      <nav className="app-nav app-nav--secondary" aria-label="Settings navigation">
        {secondaryNavigation.map((item) => <NavigationLink key={item.to} item={item} pathname={pathname} />)}
      </nav>
      <div className="app-sidebar__account"><AccountMenu /></div>
    </aside>
    <header className="app-mobile-header">
      <ApplicationBrand />
      <AccountMenu />
    </header>
    <main id="main-content" className="app-main" tabIndex={-1}>
      <RouteFocusManager />
      <Outlet />
    </main>
    <nav className="app-mobile-nav" aria-label="Mobile navigation">
      {mobileNavigation.map((item) => <NavigationLink key={item.to} item={item} mobile pathname={pathname} />)}
    </nav>
  </div>;
}
