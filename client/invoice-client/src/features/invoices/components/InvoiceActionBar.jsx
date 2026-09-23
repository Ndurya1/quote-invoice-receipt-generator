import { Link } from 'react-router-dom';
import { allowedDocumentActions, documentActionLabel } from '../../documents/documentActions.js';
import { invoiceEditPath } from '../invoiceData.js';

export default function InvoiceActionBar({ invoice, onAction, onConvert, pending = '' }) {
  const actions = allowedDocumentActions({ type: 'invoice', status: invoice.status, sourceQuoteId: invoice.source_quote_id });
  return <div className="document-action-bar" aria-label="Invoice actions">
    <div className="document-action-group document-action-group--management" aria-label="Document management actions">
      {actions.includes('edit') && <Link className="button button--secondary" to={invoiceEditPath(invoice.id)}>Edit</Link>}
      {actions.includes('delete') && <button className="button button--danger-ghost" type="button" onClick={() => onAction('delete')} disabled={Boolean(pending)}>Delete</button>}
    </div>
    <div className="document-action-group document-action-group--workflow" aria-label="Invoice workflow actions">
      {actions.includes('markSent') && <button className="button button--secondary" type="button" onClick={() => onAction('markSent')} disabled={Boolean(pending)}>{pending === 'markSent' ? 'Marking…' : documentActionLabel('markSent')}</button>}
      {actions.includes('markPaid') && <button className="button button--workflow-primary" type="button" onClick={() => onAction('markPaid')} disabled={Boolean(pending)}>{pending === 'markPaid' ? 'Recording…' : documentActionLabel('markPaid')}</button>}
      {actions.includes('cancel') && <button className="button button--danger-ghost" type="button" onClick={() => onAction('cancel')} disabled={Boolean(pending)}>{documentActionLabel('cancel')}</button>}
      {actions.includes('convertReceipt') && <button className="button button--workflow-primary" type="button" onClick={onConvert} disabled={Boolean(pending)}>{documentActionLabel('convertReceipt')}</button>}
    </div>
  </div>;
}
