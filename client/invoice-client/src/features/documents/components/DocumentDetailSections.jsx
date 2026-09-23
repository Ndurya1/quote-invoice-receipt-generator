import { formatCurrency } from '../../../utils/currencyFormat.js';
import { documentStatusLabel } from '../documentActions.js';

export function DocumentSummary({ document, type }) {
  return <section className="document-detail-card" aria-labelledby="document-summary-title">
    <h2 id="document-summary-title">Summary</h2>
    <dl>
      <div><dt>Status</dt><dd><span className="status-badge">{documentStatusLabel(document.status, type)}</span></dd></div>
      <div><dt>Issue date</dt><dd>{document.issue_date || '—'}</dd></div>
      {document.due_date && <div><dt>Due date</dt><dd>{document.due_date}</dd></div>}
      {document.expiry_date && <div><dt>Expiry date</dt><dd>{document.expiry_date}</dd></div>}
      <div><dt>Total</dt><dd>{formatCurrency(document.total, document.currency)}</dd></div>
    </dl>
  </section>;
}

export function DocumentClientSection({ client }) {
  return <section className="document-detail-card" aria-labelledby="document-client-title">
    <h2 id="document-client-title">Client</h2>
    <dl>
      <div><dt>Name</dt><dd>{client?.name || 'No client selected'}</dd></div>
      {client?.email && <div><dt>Email</dt><dd>{client.email}</dd></div>}
      {client?.phone && <div><dt>Phone</dt><dd>{client.phone}</dd></div>}
      {client?.address && <div><dt>Address</dt><dd>{client.address}</dd></div>}
    </dl>
  </section>;
}

export function DocumentRelationship({ document, type }) {
  const source = type === 'invoice' ? document.source_quote_id : document.source_invoice_id;
  if (!source) return null;
  const label = type === 'invoice' ? 'Source quotation' : 'Source invoice';
  return <section className="document-detail-card" aria-labelledby="document-relationship-title">
    <h2 id="document-relationship-title">Relationship</h2>
    <dl><div><dt>{label}</dt><dd>{source}</dd></div></dl>
  </section>;
}
