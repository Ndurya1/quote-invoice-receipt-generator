import assert from 'node:assert/strict';
import test from 'node:test';
import { canEditDocument, documentDetailPath, documentListQuery, documentStatusText, readDocumentFilters } from '../src/features/documents/documentListData.js';

test('normalizes document workspace filters by type', () => {
  const filters = readDocumentFilters(new URLSearchParams('type=invoices&status=OVERDUE&page=3&page_size=200&sort=due_date'));
  assert.deepEqual(filters, { type: 'invoices', page: 3, page_size: 100, search: '', client_id: '', status: 'OVERDUE', sort: 'due_date' });
  assert.deepEqual(documentListQuery(filters), { page: 3, page_size: 100, search: undefined, client_id: undefined, sort: 'due_date', status: 'OVERDUE' });
});

test('drops incompatible status filters when switching document types', () => {
  const filters = readDocumentFilters(new URLSearchParams('type=receipts&status=PAID&sort=total'));
  assert.equal(filters.type, 'receipts');
  assert.equal(filters.status, '');
  assert.equal(filters.sort, 'total');
  assert.equal(documentStatusText({ status: 'PAID' }, 'receipts'), 'Issued');
});

test('builds context-valid detail links and edit visibility', () => {
  const invoice = { id: 'invoice/1', status: 'DRAFT' };
  assert.equal(documentDetailPath(invoice, 'invoices'), '/documents/invoices/invoice%2F1');
  assert.equal(canEditDocument(invoice, 'invoices'), true);
  assert.equal(canEditDocument({ id: 'invoice-2', status: 'PAID' }, 'invoices'), false);
  assert.equal(canEditDocument({ id: 'receipt-1', status: 'ISSUED', source_invoice_id: 'invoice-1' }, 'receipts'), false);
});
