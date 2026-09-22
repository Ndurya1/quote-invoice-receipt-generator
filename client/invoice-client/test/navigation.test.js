import test from 'node:test';
import assert from 'node:assert/strict';
import { mobileNavigation, primaryNavigation, secondaryNavigation, isNavigationItemActive } from '../src/navigation/navigation.js';

test('defines only supported application destinations', () => {
  assert.deepEqual(primaryNavigation.map(({ label }) => label), ['Dashboard', 'Documents', 'Clients']);
  assert.deepEqual(secondaryNavigation.map(({ label }) => label), ['Business settings', 'Account']);
  assert.deepEqual(mobileNavigation.map(({ label }) => label), ['Home', 'Documents', 'Clients', 'More']);
  assert.equal(primaryNavigation.some(({ label }) => label === 'Products & services'), false);
});

test('keeps parent navigation active for nested routes', () => {
  const documents = primaryNavigation.find(({ label }) => label === 'Documents');
  const clients = primaryNavigation.find(({ label }) => label === 'Clients');
  const dashboard = primaryNavigation.find(({ label }) => label === 'Dashboard');
  assert.equal(isNavigationItemActive(documents, '/documents/quotations/123/edit'), true);
  assert.equal(isNavigationItemActive(clients, '/clients/123'), true);
  assert.equal(isNavigationItemActive(dashboard, '/documents'), false);
  assert.equal(isNavigationItemActive(dashboard, '/dashboard'), true);
});
