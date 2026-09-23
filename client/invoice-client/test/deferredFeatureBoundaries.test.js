import test from 'node:test';
import assert from 'node:assert/strict';
import { routePaths } from '../src/utils/routePaths.js';
import { primaryNavigation, secondaryNavigation } from '../src/navigation/navigation.js';

const deferredRouteFragments = [
  'forgot-password',
  'reset-password',
  'products',
  'branding',
  'reports',
  'share',
];

test('keeps backend-dependent pages out of the production route map', () => {
  const routes = Object.values(routePaths);

  for (const fragment of deferredRouteFragments) {
    assert.equal(routes.some((route) => route.includes(fragment)), false, `unexpected route: ${fragment}`);
  }
});

test('keeps backend-dependent features out of application navigation', () => {
  const labels = [...primaryNavigation, ...secondaryNavigation].map(({ label }) => label.toLowerCase());

  assert.equal(labels.some((label) => label.includes('product')), false);
  assert.equal(labels.some((label) => label.includes('branding')), false);
  assert.equal(labels.some((label) => label.includes('share')), false);
  assert.equal(labels.some((label) => label.includes('report')), false);
});
