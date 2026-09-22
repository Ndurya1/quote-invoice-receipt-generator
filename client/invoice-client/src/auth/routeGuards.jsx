import { Navigate, Outlet, useLocation } from 'react-router-dom';
import LoadingState from '../components/feedback/LoadingState.jsx';
import { routePaths } from '../utils/routePaths.js';
import { authStatuses, loginRedirect } from './authState.js';
import { useAuth } from './useAuth.js';

function AuthLoading() {
  return <div className="route-page route-page--centered"><LoadingState label="Checking your session…" /></div>;
}

export function PublicOnlyRoute() {
  const { status } = useAuth();
  if (status === authStatuses.loading) return <AuthLoading />;
  if (status === authStatuses.ready) return <Navigate replace to={routePaths.dashboard} />;
  if (status === authStatuses.needsOnboarding) return <Navigate replace to={routePaths.onboardingBusiness} />;
  return <Outlet />;
}

export function OnboardingRoute() {
  const { status } = useAuth();
  if (status === authStatuses.loading) return <AuthLoading />;
  if (status === authStatuses.anonymous) return <Navigate replace to={loginRedirect(routePaths.onboardingBusiness)} />;
  if (status === authStatuses.ready) return <Navigate replace to={routePaths.dashboard} />;
  return <Outlet />;
}

export function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();
  if (status === authStatuses.loading) return <AuthLoading />;
  if (status === authStatuses.anonymous) return <Navigate replace to={loginRedirect(`${location.pathname}${location.search}`)} />;
  if (status === authStatuses.needsOnboarding) return <Navigate replace to={routePaths.onboardingBusiness} />;
  return <Outlet />;
}
