import assert from 'node:assert/strict';
import test from 'node:test';
import { invoiceEditPath, invoiceErrorMessage, invoiceFieldErrors, invoicePath, isInvoiceEditable, validateInvoiceDates } from '../src/features/invoices/invoiceData.js';

test('builds safe invoice routes and validates due dates', () => {
  assert.equal(invoicePath('invoice/1'), '/documents/invoices/invoice%2F1');
  assert.equal(invoiceEditPath('invoice-1'), '/documents/invoices/invoice-1/edit');
  assert.deepEqual(validateInvoiceDates({ issue_date: '2026-09-20', due_date: '2026-09-19' }), { due_date: 'Due date cannot precede issue date.' });
  assert.deepEqual(validateInvoiceDates({}), { issue_date: 'Choose an issue date.' });
});

test('restricts editing to direct drafts and maps invoice errors', () => {
  assert.equal(isInvoiceEditable({ status: 'DRAFT', source_quote_id: null }), true);
  assert.equal(isInvoiceEditable({ status: 'DRAFT', source_quote_id: 'quote-1' }), false);
  assert.equal(isInvoiceEditable({ status: 'SENT', source_quote_id: null }), false);
  assert.equal(invoiceErrorMessage({ code: 'INVALID_INVOICE_STATUS', message: 'Receipt-linked invoices cannot be deleted.' }), 'Receipt-linked invoices cannot be deleted.');
  assert.deepEqual(invoiceFieldErrors({ details: { errors: [{ loc: ['body', 'due_date'], message: 'Invalid date' }] } }), { due_date: 'Invalid date' });
});
