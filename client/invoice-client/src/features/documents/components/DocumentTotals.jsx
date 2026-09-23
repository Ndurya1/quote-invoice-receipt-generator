import { formatCurrency } from '../../../utils/currencyFormat.js';

export default function DocumentTotals({ totals, currency }) {
  return (
    <aside className="document-totals" aria-labelledby="document-totals-title">
      <h2 id="document-totals-title">Totals preview</h2>
      <dl><div><dt>Subtotal</dt><dd>{formatCurrency(totals.subtotal, currency)}</dd></div><div><dt>Tax</dt><dd>{formatCurrency(totals.taxAmount, currency)}</dd></div><div><dt>Discount</dt><dd>− {formatCurrency(totals.discountAmount, currency)}</dd></div><div className="document-totals__total"><dt>Total</dt><dd>{formatCurrency(totals.total, currency)}</dd></div></dl>
      <p>Final totals are recalculated and stored by the server.</p>
    </aside>
  );
}
