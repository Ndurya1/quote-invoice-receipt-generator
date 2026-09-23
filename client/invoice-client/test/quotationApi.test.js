import assert from 'node:assert/strict';
import test from 'node:test';
import { acceptQuotation, convertQuotation, createQuotation, deleteQuotation, markQuotationSent, rejectQuotation, updateQuotation } from '../src/api/documentsApi.js';

test('maps quotation CRUD, lifecycle, and conversion calls to backend endpoints', async () => {
  const calls = [];
  const client = { request: async (path, options = {}) => { calls.push({ path, options }); return options.method === 'DELETE' ? null : { data: { id: 'quote-1' } }; } };
  await createQuotation({ client_id: 'client-1' }, client);
  await updateQuotation('quote-1', { notes: 'Updated' }, client);
  await markQuotationSent('quote-1', client);
  await acceptQuotation('quote-1', client);
  await rejectQuotation('quote-1', client);
  await convertQuotation('quote-1', { issue_date: '2026-09-23', due_date: '2026-10-23' }, client);
  await deleteQuotation('quote-1', client);
  assert.deepEqual(calls.map(({ path, options }) => [path, options.method || 'GET']), [
    ['/quotes', 'POST'], ['/quotes/quote-1', 'PATCH'], ['/quotes/quote-1/send', 'POST'], ['/quotes/quote-1/accept', 'POST'],
    ['/quotes/quote-1/reject', 'POST'], ['/quotes/quote-1/convert', 'POST'], ['/quotes/quote-1', 'DELETE'],
  ]);
  assert.deepEqual(calls[5].options.body, { issue_date: '2026-09-23', due_date: '2026-10-23' });
});
