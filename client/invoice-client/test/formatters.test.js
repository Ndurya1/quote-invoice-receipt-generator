import test from 'node:test';
import assert from 'node:assert/strict';
import { formatCurrency } from '../src/utils/currencyFormat.js';
import { formatDate, toDateInputValue } from '../src/utils/dateFormat.js';
import { documentListPath, documentTypeLabel } from '../src/utils/documentFormat.js';
import { statusLabel } from '../src/utils/statusFormat.js';

test('formats valid currency values with a currency code and two decimals', () => {
  assert.equal(formatCurrency('52500', 'KES'), 'KES 52,500.00');
  assert.equal(formatCurrency('12.5', 'USD'), 'USD 12.50');
});

test('uses a safe fallback for invalid currency display values', () => {
  assert.equal(formatCurrency('not-a-number', 'bad'), 'KES —');
});

test('formats ISO dates without timezone drift', () => {
  assert.equal(formatDate('2026-09-12'), '12 Sept 2026');
  assert.equal(formatDate(null), '—');
  assert.equal(toDateInputValue('2026-09-12T00:00:00Z'), '2026-09-12');
});

test('formats document labels, list links, and statuses', () => {
  assert.equal(documentTypeLabel('quote'), 'Quotation');
  assert.equal(documentListPath('invoices'), '/documents?type=invoices');
  assert.equal(statusLabel('REJECTED'), 'Rejected');
  assert.equal(statusLabel(null), null);
});
