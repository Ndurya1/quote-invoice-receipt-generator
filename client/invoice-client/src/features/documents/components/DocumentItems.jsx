import { formatCurrency } from '../../../utils/currencyFormat.js';

export default function DocumentItems({ items = [], currency = 'KES' }) {
  return <section className="document-detail-card document-detail-card--wide" aria-labelledby="document-items-title">
    <h2 id="document-items-title">Items</h2>
    <div className="document-items-table-wrap"><table className="document-items-table"><thead><tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Line total</th></tr></thead><tbody>{items.map((item) => <tr key={item.id || item.position || item.description}><th scope="row">{item.description}</th><td>{item.quantity}</td><td>{formatCurrency(item.unit_price, currency)}</td><td>{formatCurrency(item.line_total, currency)}</td></tr>)}</tbody></table></div>
  </section>;
}
