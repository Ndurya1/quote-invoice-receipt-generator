import test from 'node:test';
import assert from 'node:assert/strict';
import { queryKeys } from '../src/api/queryKeys.js';

test('creates deterministic filter keys', () => {
  assert.equal(queryKeys.clientsList({ search: 'Acme', page: 1 }), queryKeys.clientsList({ page: 1, search: 'Acme' }));
  assert.notEqual(queryKeys.clientsList({ page: 1 }), queryKeys.clientsList({ page: 2 }));
  assert.equal(queryKeys.invoiceDetail('invoice-1'), 'invoices:detail:invoice-1');
});
