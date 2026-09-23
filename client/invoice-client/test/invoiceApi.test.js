import assert from 'node:assert/strict';
import test from 'node:test';
import { cancelInvoice, convertInvoice, createInvoice, deleteInvoice, markInvoicePaid, markInvoiceSent, updateInvoice } from '../src/api/documentsApi.js';

test('maps invoice CRUD, lifecycle, and receipt conversion calls to backend endpoints', async () => {
  const calls = [];
  const client = { request: async (path, options = {}) => { calls.push({ path, options }); return options.method === 'DELETE' ? null : { data: { id: 'invoice-1' } }; } };
  await createInvoice({ client_id: 'client-1' }, client);
  await updateInvoice('invoice-1', { notes: 'Updated' }, client);
  await markInvoiceSent('invoice-1', client);
  await markInvoicePaid('invoice-1', client);
  await cancelInvoice('invoice-1', client);
  await convertInvoice('invoice-1', { issue_date: '2026-09-23' }, client);
  await deleteInvoice('invoice-1', client);
  assert.deepEqual(calls.map(({ path, options }) => [path, options.method || 'GET']), [
    ['/invoices', 'POST'], ['/invoices/invoice-1', 'PATCH'], ['/invoices/invoice-1/send', 'POST'], ['/invoices/invoice-1/mark-paid', 'POST'],
    ['/invoices/invoice-1/cancel', 'POST'], ['/invoices/invoice-1/convert', 'POST'], ['/invoices/invoice-1', 'DELETE'],
  ]);
  assert.deepEqual(calls[5].options.body, { issue_date: '2026-09-23' });
});
