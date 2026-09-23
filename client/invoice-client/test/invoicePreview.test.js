import assert from 'node:assert/strict';
import test from 'node:test';
import { convertPreviewInvoice, createPreviewInvoice, getPreviewInvoice, transitionPreviewInvoice, updatePreviewInvoice } from '../src/features/invoices/invoicePreview.js';
import { getPreviewReceipt } from '../src/features/receipts/receiptPreview.js';

test('provides direct and quotation-derived invoice preview fixtures', () => {
  assert.equal(getPreviewInvoice('invoice-preview-001').source_quote_id, null);
  assert.equal(getPreviewInvoice('invoice-preview-quotation-001').source_quote_id, 'quote-preview-001');
  assert.equal(getPreviewInvoice('invoice-preview-overdue-001').status, 'OVERDUE');
});

test('supports invoice preview editing, lifecycle transitions, and receipt conversion', () => {
  const created = createPreviewInvoice({ client_id: 'client-001', issue_date: '2026-09-23', due_date: '2026-10-23', currency: 'KES', tax_rate: '5.000', discount_type: 'NONE', discount_value: '0.00', items: [{ description: 'Preview work', quantity: '1', unit_price: '100.00', position: 0 }] });
  assert.equal(created.status, 'DRAFT');
  assert.equal(updatePreviewInvoice(created.id, { ...created, items: [{ description: 'Preview work', quantity: '2', unit_price: '100.00', position: 0 }] }).total, '210.00');
  assert.equal(transitionPreviewInvoice(created.id, 'PAID').status, 'PAID');
  const receipt = convertPreviewInvoice(created.id, { issue_date: '2026-09-24' });
  assert.equal(receipt.source_invoice_id, created.id);
  assert.equal(getPreviewReceipt(receipt.id).source_invoice_id, created.id);
});
