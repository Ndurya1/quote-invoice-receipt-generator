import { fieldErrorsFromDetails } from '../../api/apiErrors.js';

export const quotationListPath = '/documents?type=quotations';

export function quotationPath(id) {
  return `/documents/quotations/${encodeURIComponent(id)}`;
}

export function quotationEditPath(id) {
  return `${quotationPath(id)}/edit`;
}

export function isQuotationEditable(quotation) {
  return quotation?.status === 'DRAFT' && !quotation?.related_invoice_id;
}

export function validateQuotationDates(values = {}) {
  const errors = {};
  if (!values.issue_date) errors.issue_date = 'Choose an issue date.';
  if (values.expiry_date && values.issue_date && values.expiry_date < values.issue_date) errors.expiry_date = 'Expiry date cannot precede issue date.';
  return errors;
}

export function quotationFieldErrors(error) {
  return fieldErrorsFromDetails(error?.details);
}

export function quotationErrorMessage(error) {
  if (error?.code === 'QUOTE_NOT_FOUND') return 'This quotation could not be found or is no longer available.';
  if (error?.code === 'QUOTE_ALREADY_CONVERTED') return 'This quotation has already been converted into an invoice.';
  if (error?.code === 'INVALID_QUOTE_STATUS') return error.message || 'This quotation has changed and the requested action is no longer available.';
  return error?.message || 'Something went wrong. Please try again.';
}
