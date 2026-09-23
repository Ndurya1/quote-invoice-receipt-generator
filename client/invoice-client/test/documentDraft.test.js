import assert from 'node:assert/strict';
import test from 'node:test';
import { createDocumentDraft, hydrateDocumentDraft, serializeDocumentPayload } from '../src/features/documents/documentDraft.js';

test('creates type-specific drafts with profile currency and editable fields', () => {
  const quotation = createDocumentDraft({ type: 'quotation', businessProfile: { default_currency: 'USD' }, today: '2026-09-23' });
  assert.equal(quotation.currency, 'USD');
  assert.equal(quotation.expiry_date, '');
  assert.equal(quotation.terms, '');
  const receipt = createDocumentDraft({ type: 'receipt' });
  assert.equal(receipt.due_date, undefined);
  assert.equal(receipt.terms, undefined);
});

test('falls back safely while the business profile is still loading', () => {
  const draft = createDocumentDraft({ type: 'invoice', businessProfile: null, today: '2026-09-23' });
  assert.equal(draft.currency, 'KES');
  assert.equal(draft.due_date, '');
});

test('hydrates persisted items in position order and preserves editable values', () => {
  const draft = hydrateDocumentDraft({ client_id: 'client-1', issue_date: '2026-09-20', currency: 'KES', tax_rate: '16', discount_type: 'NONE', discount_value: '0', notes: 'Paid', items: [{ id: 'b', position: 1, description: 'Second', quantity: 2, unit_price: '20' }, { id: 'a', position: 0, description: 'First', quantity: 1, unit_price: '10' }] }, 'invoice');
  assert.deepEqual(draft.items.map((item) => item.id), ['a', 'b']);
  assert.equal(draft.items[1].unit_price, '20');
  assert.equal(draft.notes, 'Paid');
});

test('serializes only editable backend fields and excludes server-owned values', () => {
  const payload = serializeDocumentPayload({ type: 'invoice', client_id: 'client-1', issue_date: '2026-09-23', due_date: '2026-10-23', currency: 'KES', tax_rate: '16.000', discount_type: 'NONE', discount_value: '0.00', notes: '  Thank you  ', items: [{ id: 'line-1', description: 'Service', quantity: '1', unit_price: '10.00', line_total: '10.00', position: 9 }], status: 'PAID', total: '10.00', owner_id: 'owner-1' }, 'invoice');
  assert.deepEqual(payload, { client_id: 'client-1', issue_date: '2026-09-23', currency: 'KES', tax_rate: '16.000', discount_type: 'NONE', discount_value: '0.00', notes: 'Thank you', items: [{ description: 'Service', quantity: '1', unit_price: '10.00', position: 0 }], due_date: '2026-10-23', terms: null });
});
