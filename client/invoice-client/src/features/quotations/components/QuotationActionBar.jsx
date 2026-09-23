import { Link } from 'react-router-dom';
import { allowedDocumentActions, documentActionLabel } from '../../documents/documentActions.js';
import { quotationEditPath } from '../quotationData.js';

export default function QuotationActionBar({ quotation, onAction, onConvert, pending = '' }) {
  const actions = allowedDocumentActions({ type: 'quotation', status: quotation.status, relatedInvoiceId: quotation.related_invoice_id });
  return <div className="document-action-bar" aria-label="Quotation actions">
    <div className="document-action-group document-action-group--management" aria-label="Document management actions">
      {actions.includes('edit') && <Link className="button button--secondary" to={quotationEditPath(quotation.id)}>Edit</Link>}
      {actions.includes('delete') && <button className="button button--danger-ghost" type="button" onClick={() => onAction('delete')} disabled={Boolean(pending)}>Delete</button>}
    </div>
    <div className="document-action-group document-action-group--workflow" aria-label="Quotation workflow actions">
      {actions.includes('markSent') && <button className="button button--secondary" type="button" onClick={() => onAction('markSent')} disabled={Boolean(pending)}>{pending === 'markSent' ? 'Marking…' : documentActionLabel('markSent')}</button>}
      {actions.includes('accept') && <button className="button button--workflow-primary" type="button" onClick={() => onAction('accept')} disabled={Boolean(pending)}>{pending === 'accept' ? 'Accepting…' : documentActionLabel('accept')}</button>}
      {actions.includes('reject') && <button className="button button--secondary" type="button" onClick={() => onAction('reject')} disabled={Boolean(pending)}>{pending === 'reject' ? 'Rejecting…' : documentActionLabel('reject')}</button>}
      {actions.includes('convertInvoice') && <button className="button button--workflow-primary" type="button" onClick={onConvert} disabled={Boolean(pending)}>{documentActionLabel('convertInvoice')}</button>}
    </div>
  </div>;
}
