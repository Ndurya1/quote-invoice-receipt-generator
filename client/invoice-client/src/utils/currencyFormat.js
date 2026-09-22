const currencyPattern = /^[A-Z]{3}$/;

export function formatCurrency(value, currency = 'KES') {
  const safeCurrency = currencyPattern.test(currency) ? currency : 'KES';
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return `${safeCurrency} —`;
  return `${safeCurrency} ${numericValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
