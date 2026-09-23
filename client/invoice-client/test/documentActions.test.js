import assert from 'node:assert/strict';
import test from 'node:test';
import { allowedDocumentActions, documentActionLabel, documentStatusLabel } from '../src/features/documents/documentActions.js';

test('maps document lifecycle states to valid actions', () => {
  assert.deepEqual(allowedDocumentActions({ type: 'quotation', status: 'DRAFT' }), ['edit', 'delete', 'markSent']);
  assert.deepEqual(allowedDocumentActions({ type: 'quotation', status: 'SENT' }), ['accept', 'reject']);
  assert.deepEqual(allowedDocumentActions({ type: 'quotation', status: 'ACCEPTED' }), ['convertInvoice']);
  assert.deepEqual(allowedDocumentActions({ type: 'invoice', status: 'PAID' }), []);
  assert.deepEqual(allowedDocumentActions({ type: 'receipt', status: 'DRAFT', sourceInvoiceId: 'invoice-1' }), []);
});

test('keeps display labels and action labels human readable', () => {
  assert.equal(documentStatusLabel('OVERDUE', 'invoice'), 'Overdue');
  assert.equal(documentStatusLabel(null, 'receipt'), 'Issued');
  assert.equal(documentActionLabel('convertReceipt'), 'Create receipt');
});
