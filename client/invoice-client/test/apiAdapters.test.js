import test from 'node:test';
import assert from 'node:assert/strict';
import { login } from '../src/api/authApi.js';
import { createClient, listClients } from '../src/api/clientsApi.js';
import { acceptQuotation, convertInvoice, listInvoices } from '../src/api/documentsApi.js';

function stubClient() {
  const calls = [];
  const client = {
    calls,
    sessionStore: { saveTokens: (tokens) => { client.tokens = tokens; } },
    request: async (path, options = {}) => {
      calls.push({ path, options });
      if (path === '/clients' && options.method === 'POST') return { data: { id: 'client-1' } };
      if (path === '/invoices') return { data: [{ id: 'invoice-1' }], meta: { page: 1, page_size: 20, total: 1 } };
      return { data: { access_token: 'access', refresh_token: 'refresh' } };
    },
  };
  return client;
}

test('adapters map client and document requests to backend paths', async () => {
  const client = stubClient();
  await createClient({ name: 'Acme' }, client);
  await listClients({ page: 2, search: 'Acme' }, client);
  await listInvoices({ status: 'PAID' }, client);
  await acceptQuotation('quote-1', client);
  await convertInvoice('invoice-1', { issue_date: '2026-09-12' }, client);
  assert.deepEqual(client.calls.map((call) => [call.path, call.options.method]), [
    ['/clients', 'POST'],
    ['/clients', undefined],
    ['/invoices', undefined],
    ['/quotes/quote-1/accept', 'POST'],
    ['/invoices/invoice-1/convert', 'POST'],
  ]);
  assert.deepEqual(client.calls[1].options.query, { page: 2, search: 'Acme' });
  assert.deepEqual(client.calls[4].options.body, { issue_date: '2026-09-12' });
});

test('login stores the returned token pair', async () => {
  const client = stubClient();
  const tokens = await login({ email: 'm@example.com', password: 'Password1' }, client);
  assert.deepEqual(tokens, { access_token: 'access', refresh_token: 'refresh' });
  assert.deepEqual(client.tokens, tokens);
});
