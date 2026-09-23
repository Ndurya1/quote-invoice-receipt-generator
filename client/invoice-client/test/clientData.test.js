import assert from 'node:assert/strict';
import test from 'node:test';
import {
  clientDocumentsPath,
  clientEditPath,
  clientListSearchParams,
  clientFieldErrors,
  readClientListQuery,
  serializeClientCreate,
  serializeClientPatch,
  validateClientValues,
} from '../src/features/clients/clientData.js';

test('reads safe URL-backed client list filters', () => {
  const query = readClientListQuery(new URLSearchParams('page=3&page_size=50&search= Acme &sort=name'));
  assert.deepEqual(query, { page: 3, page_size: 50, search: 'Acme', sort: 'name' });
  assert.equal(clientListSearchParams(query).toString(), 'page=3&page_size=50&search=Acme&sort=name');
});

test('serializes optional client fields as nullable values', () => {
  assert.deepEqual(serializeClientCreate({ name: ' Acme ', email: ' accounts@acme.com ', phone: '', address: ' Nairobi ' }), {
    name: 'Acme', email: 'accounts@acme.com', phone: null, address: 'Nairobi',
  });
});

test('serializes only changed edit fields and allows clearing optional fields', () => {
  assert.deepEqual(serializeClientPatch({ name: 'Acme', email: '', phone: '0700', address: '' }, { name: 'Acme', email: 'a@b.com', phone: null, address: 'Nairobi' }), {
    email: null, phone: '0700', address: null,
  });
});

test('validates client fields without rejecting duplicate emails', () => {
  assert.deepEqual(validateClientValues({ name: '', email: 'not-an-email', phone: '1'.repeat(31) }), {
    name: 'Enter a client name.', email: 'Enter a valid email address.', phone: 'Phone must be 30 characters or fewer.',
  });
  assert.deepEqual(validateClientValues({ name: 'Acme', email: 'same@example.com' }), {});
});

test('builds filtered document links and maps backend field errors', () => {
  assert.equal(clientDocumentsPath('invoices', 'client-1'), '/documents?type=invoices&client_id=client-1');
  assert.equal(clientEditPath('client-1'), '/clients/client-1/edit');
  assert.deepEqual(clientFieldErrors({ details: { errors: [{ loc: ['body', 'email'], message: 'Invalid email' }] } }), { email: 'Invalid email' });
});
