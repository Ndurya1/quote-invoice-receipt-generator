import assert from 'node:assert/strict';
import test from 'node:test';
import { authStatuses } from '../src/auth/authState.js';
import { landingPrimaryAction, shouldShowPublicAuthActions } from '../src/features/landing/landingAccountActions.js';

test('uses public acquisition actions for anonymous visitors', () => {
  assert.deepEqual(landingPrimaryAction(authStatuses.anonymous), { label: 'Get started', to: '/register' });
  assert.equal(shouldShowPublicAuthActions(authStatuses.anonymous), true);
});

test('uses workspace destinations for authenticated states', () => {
  assert.deepEqual(landingPrimaryAction(authStatuses.ready), { label: 'Go to dashboard', to: '/dashboard' });
  assert.deepEqual(landingPrimaryAction(authStatuses.needsOnboarding), { label: 'Finish setup', to: '/onboarding/business' });
  assert.equal(shouldShowPublicAuthActions(authStatuses.ready), false);
});
