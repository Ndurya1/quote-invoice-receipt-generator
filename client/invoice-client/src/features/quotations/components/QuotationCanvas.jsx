import { formatCurrency } from '../../../utils/currencyFormat.js';
import { formatDate } from '../../../utils/dateFormat.js';
import { documentStatusLabel } from '../../documents/documentActions.js';

function ContactBlock({ label, name, email, phone, address }) {
  return <div className="quotation-canvas__contact"><h3>{label}</h3><strong>{name || 'Not provided'}</strong>{email && <span>{email}</span>}{phone && <span>{phone}</span>}{address && <span>{address}</span>}</div>;
}

export default function QuotationCanvas({ quotation, client, businessProfile }) {
  const taxRate = `${quotation.tax_rate || '0.000'} %`;
  return <article className="quotation-canvas" aria-labelledby="quotation-canvas-title">
    <header className="quotation-canvas__header">
      <div className="quotation-canvas__title"><h2 id="quotation-canvas-title">Quotation</h2><span>{quotation.quote_number}</span></div>
      <div className="quotation-canvas__logo">{businessProfile?.logo_url ? <img src={businessProfile.logo_url} alt={`${businessProfile.business_name || 'Business'} logo`} /> : <span>{(businessProfile?.business_name || 'Q').slice(0, 1).toUpperCase()}</span>}</div>
      <div className="quotation-canvas__metadata"><div><h3>Quotation number</h3><span>{quotation.quote_number}</span></div><div><h3>Date of issue</h3><span>{formatDate(quotation.issue_date)}</span></div><div><h3>Valid until</h3><span>{formatDate(quotation.expiry_date)}</span></div></div>
      <div className="quotation-canvas__parties"><ContactBlock label="Billed to" name={client?.name} email={client?.email} phone={client?.phone} address={client?.address} /><ContactBlock label="From" name={businessProfile?.business_name} email={businessProfile?.email} phone={businessProfile?.phone} address={businessProfile?.address} /><div className="quotation-canvas__contact"><h3>Status</h3><strong>{documentStatusLabel(quotation.status, 'quotation')}</strong><span>{quotation.currency}</span></div></div>
    </header>
    <section className="quotation-canvas__body">
      <div className="quotation-canvas__items"><table><caption className="sr-only">Quotation line items</caption><thead><tr><th scope="col">Description</th><th scope="col">Unit cost</th><th scope="col">Qty</th><th scope="col">Amount</th></tr></thead><tbody>{quotation.items.map((item) => <tr key={item.id || item.position || item.description}><th scope="row">{item.description}</th><td>{formatCurrency(item.unit_price, quotation.currency)}</td><td>{item.quantity}</td><td>{formatCurrency(item.line_total, quotation.currency)}</td></tr>)}</tbody></table></div>
      <div className="quotation-canvas__bottom"><div className="quotation-canvas__terms">{quotation.terms && <div><h3>Terms</h3><p>{quotation.terms}</p></div>}{quotation.notes && <div><h3>Notes</h3><p>{quotation.notes}</p></div>}</div><dl className="quotation-canvas__totals"><div><dt>Subtotal</dt><dd>{formatCurrency(quotation.subtotal, quotation.currency)}</dd></div><div><dt>Tax rate</dt><dd>{taxRate}</dd></div><div><dt>Tax</dt><dd>{formatCurrency(quotation.tax_amount, quotation.currency)}</dd></div>{quotation.discount_amount && quotation.discount_amount !== '0.00' && <div><dt>Discount</dt><dd>− {formatCurrency(quotation.discount_amount, quotation.currency)}</dd></div>}<div className="quotation-canvas__grand-total"><dt>Quotation total</dt><dd>{formatCurrency(quotation.total, quotation.currency)}</dd></div></dl></div>
    </section>
    <footer className="quotation-canvas__footer"><span>{businessProfile?.business_name || 'Quotation'}</span><span>{businessProfile?.email || businessProfile?.phone || ''}</span></footer>
  </article>;
}
