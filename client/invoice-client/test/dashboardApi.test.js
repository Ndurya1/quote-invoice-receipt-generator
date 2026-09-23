import assert from 'node:assert/strict';
import test from 'node:test';
import { getDashboardSummary } from '../src/api/dashboardApi.js';

test('requests the authenticated dashboard summary resource', async () => {
  const calls = [];
  const payload = { quotes: { total: 1 }, invoices: { total: 2 }, receipts: { total: 3 }, recent_documents: [] };
  const client = {
    request: async (...args) => {
      calls.push(args);
      return { data: payload };
    },
  };

  assert.deepEqual(await getDashboardSummary(client), payload);
  assert.deepEqual(calls, [['/dashboard/summary']]);
});
