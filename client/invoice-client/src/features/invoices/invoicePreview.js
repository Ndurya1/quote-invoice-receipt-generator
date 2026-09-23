import { getPreviewClient } from '../clients/clientPreview.js';
import { calculateDocumentTotals } from '../documents/documentCalculations.js';

let nextPreviewNumber = 1;
const previewStore = new Map();

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function buildInvoice(id, payload = {}, existing = {}) {
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
    source_quote_id: existing.source_quote_id ?? null,
    invoice_number: existing.invoice_number || `INV-2026-${String(nextPreviewNumber++).padStart(4, '0')}`,
    issue_date: payload.issue_date ?? existing.issue_date ?? new Date().toISOString().slice(0, 10),
    due_date: payload.due_date ?? existing.due_date ?? null,
    currency: payload.currency ?? existing.currency ?? 'KES',
    ...totals,
    status: existing.status || 'DRAFT',
    notes: payload.notes ?? existing.notes ?? null,
    terms: payload.terms ?? existing.terms ?? null,
    created_at: existing.created_at || now,
    updated_at: now,
  };
}

function seedInvoice(id, { status = 'DRAFT', sourceQuoteId = null, issueDate = '2026-09-20', dueDate = '2026-10-20' } = {}) {
  const invoice = buildInvoice(id, { client_id: 'client-001', issue_date: issueDate, due_date: dueDate, currency: 'KES', tax_rate: '5.000', items: [{ description: 'Website development', quantity: '1', unit_price: '50000.00', position: 0 }], notes: 'Thank you for your business.', terms: 'Payment is due within 5 days of receipt.' }, { status, source_quote_id: sourceQuoteId });
  previewStore.set(id, invoice);
}

function seed() {
  if (previewStore.size) return;
  seedInvoice('invoice-preview-001');
  seedInvoice('invoice-preview-quotation-001', { sourceQuoteId: 'quote-preview-001' });
  seedInvoice('invoice-preview-sent-001', { status: 'SENT' });
  seedInvoice('invoice-preview-overdue-001', { status: 'OVERDUE', dueDate: '2026-08-20' });
  seedInvoice('invoice-preview-paid-001', { status: 'PAID' });
  seedInvoice('invoice-preview-cancelled-001', { status: 'CANCELLED' });
}

export function getPreviewInvoice(id) {
  seed();
  return clone(previewStore.get(id) || buildInvoice(id));
}

export function createPreviewInvoice(payload) {
  const id = `invoice-preview-${Date.now()}`;
  const invoice = buildInvoice(id, payload);
  previewStore.set(id, invoice);
  return clone(invoice);
}

export function updatePreviewInvoice(id, payload) {
  const invoice = buildInvoice(id, payload, getPreviewInvoice(id));
  previewStore.set(id, invoice);
  return clone(invoice);
}

export function deletePreviewInvoice(id) {
  previewStore.delete(id);
}

export function transitionPreviewInvoice(id, status) {
  const invoice = getPreviewInvoice(id);
  const updated = { ...invoice, status, updated_at: new Date().toISOString() };
  previewStore.set(id, updated);
  return clone(updated);
}

export function convertPreviewInvoice(id, payload) {
  const invoice = getPreviewInvoice(id);
  return {
    id: `receipt-preview-${Date.now()}`,
    user_id: invoice.user_id,
    client_id: invoice.client_id,
    receipt_number: `RCT-2026-${String(nextPreviewNumber++).padStart(4, '0')}`,
    source_invoice_id: invoice.id,
    issue_date: payload.issue_date,
    currency: invoice.currency,
    subtotal: invoice.subtotal,
    tax_rate: invoice.tax_rate,
    tax_amount: invoice.tax_amount,
    discount_type: invoice.discount_type,
    discount_value: invoice.discount_value,
    discount_amount: invoice.discount_amount,
    total: invoice.total,
    status: null,
    notes: invoice.notes,
    items: invoice.items,
  };
}

export function getPreviewInvoiceClient(invoice) {
  return invoice ? getPreviewClient(invoice.client_id) : null;
}
