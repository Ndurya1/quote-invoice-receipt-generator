import test from 'node:test';
import assert from 'node:assert/strict';
import { authStatuses, loginRedirect, resolveAuthStatus, safeNextPath } from '../src/auth/authState.js';

test('resolves session states from token, user, and profile availability', () => {
  assert.equal(resolveAuthStatus({ hasAccessToken: false, user: null, businessProfile: null }), authStatuses.anonymous);
  assert.equal(resolveAuthStatus({ hasAccessToken: true, user: { id: '1' }, businessProfile: null }), authStatuses.needsOnboarding);
  assert.equal(resolveAuthStatus({ hasAccessToken: true, user: { id: '1' }, businessProfile: { id: '1' } }), authStatuses.ready);
});

test('creates safe login redirects and rejects external destinations', () => {
  assert.equal(safeNextPath('/documents?type=receipts'), '/documents?type=receipts');
  assert.equal(safeNextPath('https://example.com'), '/dashboard');
  assert.equal(loginRedirect('/clients'), '/login?next=%2Fclients');
  assert.equal(loginRedirect('//example.com'), '/login');
});
