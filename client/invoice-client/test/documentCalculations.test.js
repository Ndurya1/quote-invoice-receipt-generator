import assert from 'node:assert/strict';
import test from 'node:test';
import { calculateDocumentTotals, DocumentCalculationError } from '../src/features/documents/documentCalculations.js';

const base = { items: [{ description: 'Consulting', quantity: '1.005', unit_price: '1.00' }] };

test('calculates line, tax, discount, and total with server-compatible rounding', () => {
  const result = calculateDocumentTotals({ ...base, taxRate: '10.000', discountType: 'NONE', discountValue: '0.00' });
  assert.equal(result.items[0].line_total, '1.01');
  assert.equal(result.subtotal, '1.01');
  assert.equal(result.taxAmount, '0.10');
  assert.equal(result.total, '1.11');
});

test('supports fixed and percentage discounts while preventing negative totals', () => {
  const fixed = calculateDocumentTotals({ items: [{ description: 'Service', quantity: '2', unit_price: '50.00' }], discountType: 'FIXED', discountValue: '10.00' });
  assert.equal(fixed.discountAmount, '10.00');
  assert.equal(fixed.total, '90.00');
  const percentage = calculateDocumentTotals({ items: [{ description: 'Service', quantity: '2', unit_price: '50.00' }], discountType: 'PERCENTAGE', discountValue: '10.00' });
  assert.equal(percentage.discountAmount, '10.00');
  assert.equal(percentage.total, '90.00');
  assert.throws(() => calculateDocumentTotals({ ...base, discountType: 'FIXED', discountValue: '99.99' }), (error) => error instanceof DocumentCalculationError && error.code === 'INVALID_DISCOUNT');
});

test('rejects invalid quantities, descriptions, and excessive precision', () => {
  assert.throws(() => calculateDocumentTotals({ items: [{ description: 'Service', quantity: '0', unit_price: '1.00' }] }), /greater than zero/);
  assert.throws(() => calculateDocumentTotals({ items: [{ description: '', quantity: '1', unit_price: '1.00' }] }), /description/);
  assert.throws(() => calculateDocumentTotals({ items: [{ description: 'Service', quantity: '1.0001', unit_price: '1.00' }] }), /Quantity is invalid/);
});

test('rejects values outside backend numeric precision', () => {
  assert.throws(
    () => calculateDocumentTotals({ items: [{ description: 'Service', quantity: '1000000000', unit_price: '0' }] }),
    (error) => error instanceof DocumentCalculationError && error.code === 'INVALID_QUANTITY',
  );
  assert.throws(
    () => calculateDocumentTotals({ items: [{ description: 'Service', quantity: '1', unit_price: '0' }], taxRate: '1000' }),
    (error) => error instanceof DocumentCalculationError && error.code === 'INVALID_TAX_RATE',
  );
});
