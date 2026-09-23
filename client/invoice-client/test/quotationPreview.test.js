import assert from 'node:assert/strict';
import test from 'node:test';
import { convertPreviewQuotation, createPreviewQuotation, getPreviewQuotation, transitionPreviewQuotation, updatePreviewQuotation } from '../src/features/quotations/quotationPreview.js';

test('supports the quotation preview lifecycle without a backend session', () => {
  const created = createPreviewQuotation({ client_id: 'client-001', issue_date: '2026-09-23', currency: 'KES', tax_rate: '16.000', discount_type: 'NONE', discount_value: '0.00', items: [{ description: 'Preview service', quantity: '1', unit_price: '100.00', position: 0 }] });
  assert.equal(created.status, 'DRAFT');
  const updated = updatePreviewQuotation(created.id, { ...created, notes: 'Updated preview', items: [{ description: 'Preview service', quantity: '2', unit_price: '100.00', position: 0 }] });
  assert.equal(updated.total, '200.00');
  assert.equal(transitionPreviewQuotation(created.id, 'ACCEPTED').status, 'ACCEPTED');
  const invoice = convertPreviewQuotation(created.id, { issue_date: '2026-09-23', due_date: '2026-10-23' });
  assert.equal(invoice.source_quote_id, created.id);
  assert.equal(getPreviewQuotation(created.id).status, 'CONVERTED');
});
