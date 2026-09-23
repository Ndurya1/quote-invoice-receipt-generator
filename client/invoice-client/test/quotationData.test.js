import assert from 'node:assert/strict';
import test from 'node:test';
import { isQuotationEditable, quotationEditPath, quotationErrorMessage, quotationFieldErrors, quotationPath, validateQuotationDates } from '../src/features/quotations/quotationData.js';

test('builds safe quotation routes and validates quotation dates', () => {
  assert.equal(quotationPath('quote/1'), '/documents/quotations/quote%2F1');
  assert.equal(quotationEditPath('quote-1'), '/documents/quotations/quote-1/edit');
  assert.deepEqual(validateQuotationDates({ issue_date: '2026-09-20', expiry_date: '2026-09-19' }), { expiry_date: 'Expiry date cannot precede issue date.' });
  assert.deepEqual(validateQuotationDates({}), { issue_date: 'Choose an issue date.' });
});

test('only unlinked drafts are editable and backend errors remain actionable', () => {
  assert.equal(isQuotationEditable({ status: 'DRAFT' }), true);
  assert.equal(isQuotationEditable({ status: 'SENT' }), false);
  assert.equal(isQuotationEditable({ status: 'DRAFT', related_invoice_id: 'invoice-1' }), false);
  assert.equal(quotationErrorMessage({ code: 'QUOTE_ALREADY_CONVERTED' }), 'This quotation has already been converted into an invoice.');
  assert.deepEqual(quotationFieldErrors({ details: { errors: [{ loc: ['body', 'expiry_date'], message: 'Invalid date' }] } }), { expiry_date: 'Invalid date' });
});
