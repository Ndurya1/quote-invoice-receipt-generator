import { routePaths, isSafeInternalPath } from '../utils/routePaths.js';

export const authStatuses = {
  loading: 'loading',
  anonymous: 'anonymous',
  needsOnboarding: 'needsOnboarding',
  ready: 'ready',
};

export function resolveAuthStatus({ hasAccessToken, user, businessProfile }) {
  if (!hasAccessToken || !user) return authStatuses.anonymous;
  if (!businessProfile) return authStatuses.needsOnboarding;
  return authStatuses.ready;
}

export function safeNextPath(value, fallback = routePaths.dashboard) {
  return isSafeInternalPath(value) ? value : fallback;
}

export function loginRedirect(next) {
  const path = safeNextPath(next, '');
  return path ? `${routePaths.login}?next=${encodeURIComponent(path)}` : routePaths.login;
}
