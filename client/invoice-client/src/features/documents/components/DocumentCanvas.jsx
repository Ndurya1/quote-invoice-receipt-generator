import { Link } from 'react-router-dom';
import { formatCurrency } from '../../../utils/currencyFormat.js';
import { formatDate } from '../../../utils/dateFormat.js';
import { documentStatusLabel } from '../documentActions.js';

function ContactBlock({ label, name, email, phone, address }) {
  return <div className="quotation-canvas__contact"><h3>{label}</h3><strong>{name || 'Not provided'}</strong>{email && <span>{email}</span>}{phone && <span>{phone}</span>}{address && <span>{address}</span>}</div>;
}

export default function DocumentCanvas({ document, client, businessProfile, type = 'quotation' }) {
  const isInvoice = type === 'invoice';
  const isReceipt = type === 'receipt';
  const title = isInvoice ? 'Invoice' : isReceipt ? 'Receipt' : 'Quotation';
  const number = isInvoice ? document.invoice_number : isReceipt ? document.receipt_number : document.quote_number;
  const secondaryDateLabel = isInvoice ? 'Due date' : isReceipt ? null : 'Valid until';
  const secondaryDate = isInvoice ? document.due_date : document.expiry_date;
  const sourceQuotation = isInvoice && document.source_quote_id;
  const sourceInvoice = isReceipt && document.source_invoice_id;
  return <article className="quotation-canvas" aria-labelledby="document-canvas-title">
    <header className="quotation-canvas__header">
      <div className="quotation-canvas__title"><h2 id="document-canvas-title">{title}</h2><span>{number}</span></div>
      <div className="quotation-canvas__logo">{businessProfile?.logo_url ? <img src={businessProfile.logo_url} alt={`${businessProfile.business_name || 'Business'} logo`} /> : <span>{(businessProfile?.business_name || title.slice(0, 1)).slice(0, 1).toUpperCase()}</span>}</div>
      <div className={`quotation-canvas__metadata${isReceipt ? ' quotation-canvas__metadata--receipt' : ''}`}><div><h3>{isInvoice ? 'Invoice number' : isReceipt ? 'Receipt number' : 'Quotation number'}</h3><span>{number}</span></div><div><h3>Date of issue</h3><span>{formatDate(document.issue_date)}</span></div>{secondaryDateLabel && <div><h3>{secondaryDateLabel}</h3><span>{formatDate(secondaryDate)}</span></div>}</div>
      <div className="quotation-canvas__parties"><ContactBlock label="Billed to" name={client?.name} email={client?.email} phone={client?.phone} address={client?.address} /><ContactBlock label="From" name={businessProfile?.business_name} email={businessProfile?.email} phone={businessProfile?.phone} address={businessProfile?.address} /><div className="quotation-canvas__contact"><h3>Status</h3><strong>{documentStatusLabel(document.status, type)}</strong><span>{document.currency}</span></div></div>
      {sourceQuotation && <div className="quotation-canvas__relationship"><span>Source quotation</span><Link to={`/documents/quotations/${encodeURIComponent(sourceQuotation)}`}>Open {sourceQuotation}</Link></div>}
      {sourceInvoice && <div className="quotation-canvas__relationship"><span>Source invoice</span><Link to={`/documents/invoices/${encodeURIComponent(sourceInvoice)}`}>Open {sourceInvoice}</Link></div>}
    </header>
    <section className="quotation-canvas__body">
      <div className="quotation-canvas__items"><table><caption className="sr-only">{title} line items</caption><thead><tr><th scope="col">Description</th><th scope="col">Unit cost</th><th scope="col">Qty</th><th scope="col">Amount</th></tr></thead><tbody>{(document.items || []).map((item) => <tr key={item.id || item.position || item.description}><th scope="row">{item.description}</th><td>{formatCurrency(item.unit_price, document.currency)}</td><td>{item.quantity}</td><td>{formatCurrency(item.line_total, document.currency)}</td></tr>)}</tbody></table></div>
      <div className="quotation-canvas__bottom"><div className="quotation-canvas__terms">{document.terms && <div><h3>Terms</h3><p>{document.terms}</p></div>}{document.notes && <div><h3>Notes</h3><p>{document.notes}</p></div>}</div><dl className="quotation-canvas__totals"><div><dt>Subtotal</dt><dd>{formatCurrency(document.subtotal, document.currency)}</dd></div><div><dt>Tax rate</dt><dd>{`${document.tax_rate || '0.000'} %`}</dd></div><div><dt>Tax</dt><dd>{formatCurrency(document.tax_amount, document.currency)}</dd></div>{document.discount_amount && document.discount_amount !== '0.00' && <div><dt>Discount</dt><dd>- {formatCurrency(document.discount_amount, document.currency)}</dd></div>}<div className="quotation-canvas__grand-total"><dt>{isInvoice ? 'Invoice total' : isReceipt ? 'Receipt total' : 'Quotation total'}</dt><dd>{formatCurrency(document.total, document.currency)}</dd></div></dl></div>
    </section>
    <footer className="quotation-canvas__footer"><span>{businessProfile?.business_name || title}</span><span>{businessProfile?.email || businessProfile?.phone || ''}</span></footer>
  </article>;
}
