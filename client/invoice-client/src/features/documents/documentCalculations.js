import { compareScaled, formatScaled, multiplyToScale, roundHalfUp, toScaledInteger } from './decimal.js';

export class DocumentCalculationError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'DocumentCalculationError';
    this.code = code;
  }
}

const MAX_MONEY = 99999999999999n;

function safeScaled(value, scale, code, label) {
  try {
    return toScaledInteger(value, scale);
  } catch (error) {
    throw new DocumentCalculationError(code, `${label} is invalid.`, { cause: error });
  }
}

function lineTotal(item) {
  const quantity = safeScaled(item.quantity, 3, 'INVALID_QUANTITY', 'Quantity');
  const unitPrice = safeScaled(item.unit_price, 2, 'INVALID_UNIT_PRICE', 'Unit price');
  if (quantity <= 0n) throw new DocumentCalculationError('INVALID_QUANTITY', 'Quantity must be greater than zero.');
  if (unitPrice < 0n) throw new DocumentCalculationError('INVALID_UNIT_PRICE', 'Unit price cannot be negative.');
  const total = multiplyToScale(item.quantity, item.unit_price, 2);
  if (total > MAX_MONEY) throw new DocumentCalculationError('LINE_TOTAL_OUT_OF_RANGE', 'Line total exceeds the supported monetary range.');
  return total;
}

export function calculateDocumentTotals({ items = [], taxRate = '0', discountType = 'NONE', discountValue = '0' } = {}) {
  if (!Array.isArray(items) || items.length === 0) throw new DocumentCalculationError('EMPTY_LINE_ITEMS', 'At least one line item is required.');
  const calculatedItems = items.map((item, index) => {
    if (!String(item.description || '').trim()) throw new DocumentCalculationError('INVALID_DESCRIPTION', 'Each line item needs a description.');
    return { ...item, position: index, line_total: formatScaled(lineTotal(item), 2) };
  });
  const subtotal = calculatedItems.reduce((sum, item) => sum + toScaledInteger(item.line_total, 2), 0n);
  if (subtotal > MAX_MONEY) throw new DocumentCalculationError('SUBTOTAL_OUT_OF_RANGE', 'Subtotal exceeds the supported monetary range.');

  const rate = safeScaled(taxRate, 3, 'INVALID_TAX_RATE', 'Tax rate');
  if (rate < 0n) throw new DocumentCalculationError('INVALID_TAX_RATE', 'Tax rate cannot be negative.');
  const taxAmount = roundHalfUp(subtotal * rate, 100n * 1000n);
  let discountAmount = 0n;
  if (!['NONE', 'FIXED', 'PERCENTAGE'].includes(discountType)) throw new DocumentCalculationError('INVALID_DISCOUNT', 'Discount type is invalid.');
  if (discountType === 'NONE') {
    if (safeScaled(discountValue, 2, 'INVALID_DISCOUNT', 'Discount value') !== 0n) throw new DocumentCalculationError('INVALID_DISCOUNT', 'NONE requires a zero discount value.');
  } else if (discountType === 'FIXED') {
    discountAmount = safeScaled(discountValue, 2, 'INVALID_DISCOUNT', 'Discount value');
  } else {
    const percentage = safeScaled(discountValue, 2, 'INVALID_DISCOUNT', 'Discount value');
    if (percentage < 0n || percentage > 10000n) throw new DocumentCalculationError('INVALID_DISCOUNT', 'Percentage discount cannot exceed 100.');
    discountAmount = roundHalfUp(subtotal * percentage, 100n * 100n);
  }
  if (discountAmount < 0n || compareScaled(discountAmount, subtotal + taxAmount) > 0) throw new DocumentCalculationError('INVALID_DISCOUNT', 'Discount cannot make the final total negative.');
  const total = subtotal + taxAmount - discountAmount;
  if (total > MAX_MONEY) throw new DocumentCalculationError('TOTAL_OUT_OF_RANGE', 'Total exceeds the supported monetary range.');
  return {
    items: calculatedItems,
    subtotal: formatScaled(subtotal, 2),
    taxRate: formatScaled(rate, 3),
    taxAmount: formatScaled(taxAmount, 2),
    discountType,
    discountValue: formatScaled(safeScaled(discountValue, 2, 'INVALID_DISCOUNT', 'Discount value'), 2),
    discountAmount: formatScaled(discountAmount, 2),
    total: formatScaled(total, 2),
  };
}
