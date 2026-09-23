import { authStatuses } from '../../auth/authState.js';
import { routePaths } from '../../utils/routePaths.js';

export function landingPrimaryAction(status) {
  if (status === authStatuses.ready) return { label: 'Go to dashboard', to: routePaths.dashboard };
  if (status === authStatuses.needsOnboarding) return { label: 'Finish setup', to: routePaths.onboardingBusiness };
  return { label: 'Get started', to: routePaths.register };
}

export function shouldShowPublicAuthActions(status) {
  return status === authStatuses.anonymous || status === authStatuses.loading;
}
