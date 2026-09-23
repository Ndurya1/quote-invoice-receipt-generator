import assert from 'node:assert/strict';
import test from 'node:test';
import { listPreviewDocuments } from '../src/features/documents/documentListPreview.js';

const clients = { 'client-1': { name: 'Acme Limited' }, 'client-2': { name: 'Future Works' } };
const documents = [
  { id: 'invoice-1', invoice_number: 'INV-001', client_id: 'client-1', status: 'OVERDUE', total: '900.00', created_at: '2026-09-01', notes: 'Retainer' },
  { id: 'invoice-2', invoice_number: 'INV-002', client_id: 'client-2', status: 'PAID', total: '1200.00', created_at: '2026-09-02', notes: 'Implementation' },
  { id: 'invoice-3', invoice_number: 'INV-003', client_id: 'client-1', status: 'OVERDUE', total: '300.00', created_at: '2026-09-03', notes: 'Support' },
];

test('filters, sorts and paginates preview documents with client names', () => {
  const result = listPreviewDocuments(documents, { status: 'OVERDUE', search: 'acme', page: 1, page_size: 1, sort: '-created_at' }, (id) => clients[id], 'invoice_number');
  assert.equal(result.meta.total, 2);
  assert.equal(result.data.length, 1);
  assert.equal(result.data[0].id, 'invoice-3');
  assert.equal(result.data[0].client_name, 'Acme Limited');
});

test('does not mutate source preview documents while sorting', () => {
  const source = documents.map((document) => ({ ...document }));
  listPreviewDocuments(documents, { sort: 'invoice_number' }, (id) => clients[id], 'invoice_number');
  assert.deepEqual(documents, source);
});
