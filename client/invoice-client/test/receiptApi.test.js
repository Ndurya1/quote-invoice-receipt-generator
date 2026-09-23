import assert from 'node:assert/strict';
import test from 'node:test';
import { createReceipt, deleteReceipt, getReceipt, listReceipts, updateReceipt } from '../src/api/documentsApi.js';

test('maps receipt CRUD calls to backend endpoints', async () => {
  const calls = [];
  const client = { request: async (path, options = {}) => { calls.push({ path, options }); return options.method === 'DELETE' ? null : { data: { id: 'receipt-1' } }; } };
  await listReceipts({ page: 1 }, client);
  await getReceipt('receipt-1', client);
  await createReceipt({ client_id: 'client-1' }, client);
  await updateReceipt('receipt-1', { notes: 'Updated' }, client);
  await deleteReceipt('receipt-1', client);
  assert.deepEqual(calls.map(({ path, options }) => [path, options.method || 'GET']), [
    ['/receipts', 'GET'], ['/receipts/receipt-1', 'GET'], ['/receipts', 'POST'], ['/receipts/receipt-1', 'PATCH'], ['/receipts/receipt-1', 'DELETE'],
  ]);
});
