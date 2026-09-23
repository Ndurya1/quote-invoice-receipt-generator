import assert from 'node:assert/strict';
import test from 'node:test';
import { isReceiptEditable, receiptEditPath, receiptErrorMessage, receiptPath, validateReceiptDates } from '../src/features/receipts/receiptData.js';

test('builds receipt routes and validates issue dates', () => {
  assert.equal(receiptPath('receipt/1'), '/documents/receipts/receipt%2F1');
  assert.equal(receiptEditPath('receipt-1'), '/documents/receipts/receipt-1/edit');
  assert.deepEqual(validateReceiptDates({}), { issue_date: 'Choose an issue date.' });
  assert.deepEqual(validateReceiptDates({ issue_date: '2026-09-23' }), {});
});

test('keeps invoice-linked receipts immutable and maps backend errors', () => {
  assert.equal(isReceiptEditable({ source_invoice_id: null }), true);
  assert.equal(isReceiptEditable({ source_invoice_id: 'invoice-1' }), false);
  assert.equal(receiptErrorMessage({ code: 'RECEIPT_NOT_FOUND' }), 'This receipt could not be found or is no longer available.');
  assert.equal(receiptErrorMessage({ code: 'INVALID_RECEIPT_STATUS', message: 'Linked.' }), 'Linked.');
});
