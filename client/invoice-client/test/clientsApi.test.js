import assert from 'node:assert/strict';
import test from 'node:test';
import { createClient, deleteClient, getClient, listClients, updateClient } from '../src/api/clientsApi.js';

test('maps client CRUD operations to owner-scoped API paths', async () => {
  const calls = [];
  const client = {
    request: async (...args) => {
      calls.push(args);
      if (args[0] === '/clients' && !args[1]?.method) return { data: [{ id: '1' }], meta: { page: 2, page_size: 10, total: 12 } };
      if (args[1]?.method === 'DELETE') return null;
      return { data: { id: '1', name: 'Acme' } };
    },
  };

  assert.deepEqual(await listClients({ page: 2, page_size: 10 }, client), { data: [{ id: '1' }], meta: { page: 2, page_size: 10, total: 12 } });
  assert.deepEqual(await getClient('1', client), { id: '1', name: 'Acme' });
  assert.deepEqual(await createClient({ name: 'Acme' }, client), { id: '1', name: 'Acme' });
  assert.deepEqual(await updateClient('1', { phone: null }, client), { id: '1', name: 'Acme' });
  assert.equal(await deleteClient('1', client), undefined);
  assert.deepEqual(calls.map(([path, options]) => [path, options?.method || 'GET']), [
    ['/clients', 'GET'],
    ['/clients/1', 'GET'],
    ['/clients', 'POST'],
    ['/clients/1', 'PATCH'],
    ['/clients/1', 'DELETE'],
  ]);
});
