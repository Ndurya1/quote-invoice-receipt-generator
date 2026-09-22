import { routePaths } from '../utils/routePaths.js';

export const primaryNavigation = [
  { label: 'Dashboard', to: routePaths.dashboard, end: true },
  { label: 'Documents', to: routePaths.documents },
  { label: 'Clients', to: routePaths.clients },
];

export const secondaryNavigation = [
  { label: 'Business settings', to: routePaths.businessSettings, end: true },
  { label: 'Account', to: routePaths.accountSettings, end: true },
];

export const mobileNavigation = [
  { label: 'Home', to: routePaths.dashboard, end: true },
  { label: 'Documents', to: routePaths.documents },
  { label: 'Clients', to: routePaths.clients },
  { label: 'More', to: routePaths.accountSettings, end: true },
];

export function isNavigationItemActive(item, pathname) {
  if (item.end) return pathname === item.to;
  return pathname === item.to || pathname.startsWith(`${item.to}/`);
}
