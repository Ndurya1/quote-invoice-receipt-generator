import { fieldErrorsFromDetails } from '../../api/apiErrors.js';

export const invoiceListPath = '/documents?type=invoices';

export function invoicePath(id) {
  return `/documents/invoices/${encodeURIComponent(id)}`;
}

export function invoiceEditPath(id) {
  return `${invoicePath(id)}/edit`;
}

export function isInvoiceEditable(invoice) {
  return invoice?.status === 'DRAFT' && !invoice?.source_quote_id;
}

export function validateInvoiceDates(values = {}) {
  const errors = {};
  if (!values.issue_date) errors.issue_date = 'Choose an issue date.';
  if (values.due_date && values.issue_date && values.due_date < values.issue_date) errors.due_date = 'Due date cannot precede issue date.';
  return errors;
}

export function invoiceFieldErrors(error) {
  return fieldErrorsFromDetails(error?.details);
}

export function invoiceErrorMessage(error) {
  if (error?.code === 'INVOICE_NOT_FOUND') return 'This invoice could not be found or is no longer available.';
  if (error?.code === 'INVALID_INVOICE_STATUS') return error.message || 'This invoice has changed and the requested action is no longer available.';
  return error?.message || 'Something went wrong. Please try again.';
}
