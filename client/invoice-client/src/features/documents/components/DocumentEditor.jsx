import { useMemo } from 'react';
import ClientSelector from './ClientSelector.jsx';
import DocumentTotals from './DocumentTotals.jsx';
import LineItemsEditor from './LineItemsEditor.jsx';
import TaxDiscountFields from './TaxDiscountFields.jsx';
import { calculateDocumentTotals } from '../documentCalculations.js';
import { documentConfig, serializeDocumentPayload } from '../documentDraft.js';

export default function DocumentEditor({ draft, client, onChange, onSubmit, onAddClient, onClientChange, submitting = false, message = '' }) {
  const config = documentConfig(draft.type);
  const totals = useMemo(() => {
    try {
      return { ...calculateDocumentTotals({ items: draft.items, taxRate: draft.tax_rate, discountType: draft.discount_type, discountValue: draft.discount_value }), error: '' };
    } catch (error) {
      return { subtotal: '0.00', taxAmount: '0.00', discountAmount: '0.00', total: '0.00', error: error.message };
    }
  }, [draft]);

  function update(values) { onChange({ ...draft, ...values }); }

  function submit(event) {
    event.preventDefault();
    onSubmit(serializeDocumentPayload(draft, draft.type));
  }

  return (
    <form className="document-editor" onSubmit={submit}>
      {message && <div className="alert alert--success" role="status">{message}</div>}
      <section className="document-form-section" aria-labelledby="document-details-title">
        <div className="document-form-section__heading"><h2 id="document-details-title">Document details</h2><p>Choose the client, date, and currency for this {config.label.toLowerCase()}.</p></div>
        <ClientSelector value={draft.client_id} selectedClient={client} onChange={(client_id, selectedClient) => (onClientChange ? onClientChange(client_id, selectedClient) : update({ client_id }))} onAddClient={onAddClient} />
        <div className="document-metadata-grid"><label className="field"><span className="field__label">Issue date *</span><input type="date" value={draft.issue_date} onChange={(event) => update({ issue_date: event.target.value })} /></label><label className="field"><span className="field__label">Currency *</span><input value={draft.currency} maxLength="3" onChange={(event) => update({ currency: event.target.value.toUpperCase() })} /></label>{config.dateField && <label className="field"><span className="field__label">{config.dateField === 'expiry_date' ? 'Expiry date' : 'Due date'}</span><input type="date" value={draft[config.dateField]} min={draft.issue_date} onChange={(event) => update({ [config.dateField]: event.target.value })} /></label>}</div>
      </section>
      <LineItemsEditor items={draft.items} onChange={(items) => update({ items })} />
      <TaxDiscountFields draft={draft} onChange={update} />
      <section className="document-form-section" aria-labelledby="document-notes-title"><div className="document-form-section__heading"><h2 id="document-notes-title">Notes and terms</h2></div><label className="field"><span className="field__label">Notes</span><textarea value={draft.notes} onChange={(event) => update({ notes: event.target.value })} /></label>{config.hasTerms && <label className="field"><span className="field__label">Terms</span><textarea value={draft.terms} onChange={(event) => update({ terms: event.target.value })} /></label>}</section>
      {totals.error && <div className="form-error" role="alert">{totals.error}</div>}
      <div className="document-editor__footer"><DocumentTotals totals={totals} currency={draft.currency} /><div className="document-editor__actions"><button className="button button--secondary" type="button" onClick={onAddClient}>Add client</button><button className="button" type="submit" disabled={submitting || Boolean(totals.error)}>{submitting ? 'Saving…' : 'Save preview'}</button></div></div>
    </form>
  );
}
