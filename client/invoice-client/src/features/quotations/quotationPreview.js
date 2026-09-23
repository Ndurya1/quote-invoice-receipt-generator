import { calculateDocumentTotals } from '../documents/documentCalculations.js';
import { getPreviewClient } from '../clients/clientPreview.js';

let nextPreviewNumber = 2;
const previewStore = new Map();

function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function buildQuotation(id, payload = {}, existing = {}) {
  const totals = calculateDocumentTotals({
    items: payload.items || existing.items || [{ description: 'Design consultation', quantity: '1', unit_price: '2500.00' }],
    taxRate: payload.tax_rate ?? existing.tax_rate ?? '0.000',
    discountType: payload.discount_type ?? existing.discount_type ?? 'NONE',
    discountValue: payload.discount_value ?? existing.discount_value ?? '0.00',
  });
  const now = new Date().toISOString();
  return {
    ...existing,
    id,
    user_id: 'developer-preview-user',
    client_id: payload.client_id ?? existing.client_id ?? 'client-001',
    quote_number: existing.quote_number || `Q-2026-${String(nextPreviewNumber++).padStart(4, '0')}`,
    issue_date: payload.issue_date ?? existing.issue_date ?? new Date().toISOString().slice(0, 10),
    expiry_date: payload.expiry_date ?? existing.expiry_date ?? null,
    currency: payload.currency ?? existing.currency ?? 'KES',
    ...totals,
    status: existing.status || 'DRAFT',
    notes: payload.notes ?? existing.notes ?? null,
    terms: payload.terms ?? existing.terms ?? null,
    created_at: existing.created_at || now,
    updated_at: now,
  };
}

function seed() {
  if (!previewStore.has('quote-preview-001')) {
    previewStore.set('quote-preview-001', buildQuotation('quote-preview-001', {
      client_id: 'client-001', issue_date: '2026-09-20', expiry_date: '2026-10-20', currency: 'KES', tax_rate: '16.000',
      items: [{ description: 'Brand identity package', quantity: '1', unit_price: '45000.00', position: 0 }],
      notes: 'Thank you for considering this proposal.', terms: 'Payment is due within 14 days of invoice date.',
    }));
  }
}

export function getPreviewQuotation(id) {
  seed();
  const existing = previewStore.get(id);
  return clone(existing || buildQuotation(id));
}

export function createPreviewQuotation(payload) {
  const id = `quote-preview-${Date.now()}`;
  const quotation = buildQuotation(id, payload);
  previewStore.set(id, quotation);
  return clone(quotation);
}

export function updatePreviewQuotation(id, payload) {
  const updated = buildQuotation(id, payload, getPreviewQuotation(id));
  previewStore.set(id, updated);
  return clone(updated);
}

export function deletePreviewQuotation(id) {
  previewStore.delete(id);
}

export function transitionPreviewQuotation(id, status) {
  const quotation = getPreviewQuotation(id);
  const updated = { ...quotation, status, updated_at: new Date().toISOString() };
  previewStore.set(id, updated);
  return clone(updated);
}

export function convertPreviewQuotation(id, payload) {
  const quotation = transitionPreviewQuotation(id, 'CONVERTED');
  return {
    id: `invoice-preview-${Date.now()}`,
    user_id: quotation.user_id,
    client_id: quotation.client_id,
    invoice_number: `INV-2026-${String(nextPreviewNumber++).padStart(4, '0')}`,
    source_quote_id: quotation.id,
    issue_date: payload.issue_date,
    due_date: payload.due_date || null,
    currency: quotation.currency,
    subtotal: quotation.subtotal,
    tax_rate: quotation.tax_rate,
    tax_amount: quotation.tax_amount,
    discount_type: quotation.discount_type,
    discount_value: quotation.discount_value,
    discount_amount: quotation.discount_amount,
    total: quotation.total,
    status: 'DRAFT',
    notes: quotation.notes,
    terms: quotation.terms,
    items: quotation.items.map((item, index) => ({ ...item, position: index })),
  };
}

export function getPreviewQuotationClient(quotation) {
  return quotation ? getPreviewClient(quotation.client_id) : null;
}
