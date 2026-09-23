import assert from 'node:assert/strict';
import test from 'node:test';
import { createPreviewReceipt, createPreviewReceiptFromInvoice, deletePreviewReceipt, getPreviewReceipt, updatePreviewReceipt } from '../src/features/receipts/receiptPreview.js';

test('provides direct and invoice-linked receipt preview fixtures', () => {
  assert.equal(getPreviewReceipt('receipt-preview-001').source_invoice_id, null);
  assert.equal(getPreviewReceipt('receipt-preview-invoice-001').source_invoice_id, 'invoice-preview-paid-001');
});

test('supports direct receipt preview editing and protects linked receipts', () => {
  const created = createPreviewReceipt({ client_id: 'client-001', issue_date: '2026-09-23', currency: 'KES', items: [{ description: 'Preview payment', quantity: '1', unit_price: '100.00', position: 0 }] });
  assert.equal(updatePreviewReceipt(created.id, { notes: 'Recorded' }).notes, 'Recorded');
  assert.throws(() => updatePreviewReceipt('receipt-preview-invoice-001', { notes: 'Nope' }), (error) => error.code === 'INVALID_RECEIPT_STATUS');
  deletePreviewReceipt(created.id);
  assert.equal(getPreviewReceipt(created.id).id, created.id);
});

test('stores receipts created from invoices in the preview store', () => {
  const receipt = createPreviewReceiptFromInvoice({ id: 'invoice-preview-test', client_id: 'client-001', currency: 'KES', tax_rate: '0.000', discount_type: 'NONE', discount_value: '0.00', notes: 'Paid', items: [{ description: 'Work', quantity: '1', unit_price: '50.00', position: 0 }] }, { issue_date: '2026-09-23' });
  assert.equal(getPreviewReceipt(receipt.id).source_invoice_id, 'invoice-preview-test');
});
