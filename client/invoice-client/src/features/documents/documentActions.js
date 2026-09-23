import { statusLabel } from '../../utils/statusFormat.js';

const actionLabels = {
  edit: 'Edit', delete: 'Delete', markSent: 'Mark as sent', accept: 'Accept', reject: 'Reject',
  convertInvoice: 'Create invoice', markPaid: 'Mark as paid', cancel: 'Cancel invoice', convertReceipt: 'Create receipt',
};

export function documentStatusLabel(status, type) {
  if (status) return statusLabel(status);
  return type === 'receipt' ? 'Issued' : 'Draft';
}

export function allowedDocumentActions({ type, status = 'DRAFT', sourceQuoteId = null, sourceInvoiceId = null } = {}) {
  if (type === 'quotation') {
    if (status === 'DRAFT') return ['edit', 'delete', 'markSent', 'accept'];
    if (status === 'SENT') return ['accept', 'reject'];
    if (status === 'ACCEPTED') return ['convertInvoice'];
    return [];
  }
  if (type === 'invoice') {
    if (status === 'DRAFT' && sourceQuoteId) return ['markSent', 'cancel', 'convertReceipt'];
    if (status === 'DRAFT') return ['edit', 'delete', 'markSent', 'cancel', 'convertReceipt'];
    if (status === 'SENT' || status === 'OVERDUE') return ['markPaid', 'cancel', 'convertReceipt'];
    if (status === 'PAID') return ['convertReceipt'];
    return [];
  }
  if (type === 'receipt') return sourceInvoiceId ? [] : ['edit', 'delete'];
  return [];
}

export function documentActionLabel(action) {
  return actionLabels[action] || action;
}
