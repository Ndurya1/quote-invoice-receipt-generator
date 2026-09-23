import { getPreviewClient } from '../clients/clientPreview.js';
import { calculateDocumentTotals } from '../documents/documentCalculations.js';

let nextPreviewNumber = 1;
const previewStore = new Map();

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function buildReceipt(id, payload = {}, existing = {}) {
  const totals = calculateDocumentTotals({
    items: payload.items || existing.items || [{ description: 'Website development', quantity: '1', unit_price: '50000.00' }],
    taxRate: payload.tax_rate ?? existing.tax_rate ?? '5.000',
    discountType: payload.discount_type ?? existing.discount_type ?? 'NONE',
    discountValue: payload.discount_value ?? existing.discount_value ?? '0.00',
  });
  const now = new Date().toISOString();
  return {
    ...existing,
    id,
    user_id: 'developer-preview-user',
    client_id: payload.client_id ?? existing.client_id ?? 'client-001',
    source_invoice_id: payload.source_invoice_id ?? existing.source_invoice_id ?? null,
    receipt_number: existing.receipt_number || `RCT-2026-${String(nextPreviewNumber++).padStart(4, '0')}`,
    issue_date: payload.issue_date ?? existing.issue_date ?? new Date().toISOString().slice(0, 10),
    currency: payload.currency ?? existing.currency ?? 'KES',
    items: totals.items,
    subtotal: totals.subtotal,
    tax_rate: totals.taxRate,
    tax_amount: totals.taxAmount,
    discount_type: totals.discountType,
    discount_value: totals.discountValue,
    discount_amount: totals.discountAmount,
    total: totals.total,
    notes: payload.notes ?? existing.notes ?? null,
    created_at: existing.created_at || now,
    updated_at: now,
  };
}

function seed() {
  if (previewStore.size) return;
  previewStore.set('receipt-preview-001', buildReceipt('receipt-preview-001', {
    client_id: 'client-001', issue_date: '2026-09-22', currency: 'KES', tax_rate: '5.000',
    items: [{ description: 'Website development', quantity: '1', unit_price: '50000.00', position: 0 }],
    notes: 'Payment received with thanks.',
  }));
  previewStore.set('receipt-preview-invoice-001', buildReceipt('receipt-preview-invoice-001', {
    client_id: 'client-001', source_invoice_id: 'invoice-preview-paid-001', issue_date: '2026-09-23', currency: 'KES', tax_rate: '5.000',
    items: [{ description: 'Website development', quantity: '1', unit_price: '50000.00', position: 0 }],
    notes: 'Payment received for invoice INV-2026-0004.',
  }));
}

export function getPreviewReceipt(id) {
  seed();
  return clone(previewStore.get(id) || buildReceipt(id));
}

export function createPreviewReceipt(payload) {
  const id = `receipt-preview-${Date.now()}`;
  const receipt = buildReceipt(id, payload);
  previewStore.set(id, receipt);
  return clone(receipt);
}

export function createPreviewReceiptFromInvoice(invoice, payload) {
  const id = `receipt-preview-${Date.now()}`;
  const receipt = buildReceipt(id, {
    ...payload,
    client_id: invoice.client_id,
    source_invoice_id: invoice.id,
    currency: invoice.currency,
    tax_rate: invoice.tax_rate ?? invoice.taxRate,
    discount_type: invoice.discount_type ?? invoice.discountType,
    discount_value: invoice.discount_value ?? invoice.discountValue,
    notes: invoice.notes,
    items: invoice.items,
  });
  previewStore.set(id, receipt);
  return clone(receipt);
}

export function updatePreviewReceipt(id, payload) {
  const receipt = getPreviewReceipt(id);
  if (receipt.source_invoice_id) throw Object.assign(new Error('Invoice-linked receipts cannot be changed or deleted.'), { code: 'INVALID_RECEIPT_STATUS', status: 409 });
  const updated = buildReceipt(id, payload, receipt);
  previewStore.set(id, updated);
  return clone(updated);
}

export function deletePreviewReceipt(id) {
  const receipt = getPreviewReceipt(id);
  if (receipt.source_invoice_id) throw Object.assign(new Error('Invoice-linked receipts cannot be changed or deleted.'), { code: 'INVALID_RECEIPT_STATUS', status: 409 });
  previewStore.delete(id);
}

export function getPreviewReceiptClient(receipt) {
  return receipt ? getPreviewClient(receipt.client_id) : null;
}
