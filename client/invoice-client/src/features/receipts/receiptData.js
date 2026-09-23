import { fieldErrorsFromDetails } from '../../api/apiErrors.js';

export const receiptListPath = '/documents?type=receipts';

export function receiptPath(id) {
  return `/documents/receipts/${encodeURIComponent(id)}`;
}

export function receiptEditPath(id) {
  return `${receiptPath(id)}/edit`;
}

export function isReceiptEditable(receipt) {
  return Boolean(receipt) && !receipt.source_invoice_id;
}

export function validateReceiptDates(values = {}) {
  return values.issue_date ? {} : { issue_date: 'Choose an issue date.' };
}

export function receiptFieldErrors(error) {
  return fieldErrorsFromDetails(error?.details);
}

export function receiptErrorMessage(error) {
  if (error?.code === 'RECEIPT_NOT_FOUND') return 'This receipt could not be found or is no longer available.';
  if (error?.code === 'INVALID_RECEIPT_STATUS') return error.message || 'This receipt is linked to an invoice and can no longer be changed.';
  return error?.message || 'Something went wrong. Please try again.';
}
