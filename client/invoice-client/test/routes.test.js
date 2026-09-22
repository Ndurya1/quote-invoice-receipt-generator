import test from 'node:test';
import assert from 'node:assert/strict';
import { isSafeInternalPath, routePaths } from '../src/utils/routePaths.js';

test('defines the public and protected route map', () => {
  assert.equal(routePaths.home, '/');
  assert.equal(routePaths.register, '/register');
  assert.equal(routePaths.dashboard, '/dashboard');
  assert.equal(routePaths.quotationDetail, '/documents/quotations/:quoteId');
  assert.equal(routePaths.clientEdit, '/clients/:clientId/edit');
});

test('accepts only internal next destinations', () => {
  assert.equal(isSafeInternalPath('/dashboard'), true);
  assert.equal(isSafeInternalPath('/documents?type=receipts'), true);
  assert.equal(isSafeInternalPath('https://example.com'), false);
  assert.equal(isSafeInternalPath('//example.com'), false);
  assert.equal(isSafeInternalPath(null), false);
});
