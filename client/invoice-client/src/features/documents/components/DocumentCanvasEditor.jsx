import { ArrowDown, ArrowUp, Trash2 } from 'lucide-react';
import { formatCurrency } from '../../../utils/currencyFormat.js';
import { createLineItem, documentConfig } from '../documentDraft.js';
import ClientSelector from './ClientSelector.jsx';
import DocumentTotals from './DocumentTotals.jsx';

function ContactBlock({ label, name, email, phone, address }) {
  return <div className="quotation-canvas__contact"><h3>{label}</h3><strong>{name || 'Not provided'}</strong>{email && <span>{email}</span>}{phone && <span>{phone}</span>}{address && <span>{address}</span>}</div>;
}

export default function DocumentCanvasEditor({ draft, client, businessProfile, totals, onChange, onAddClient, onClientChange, message = '', error = '', totalsError = '', submitting = false }) {
  const config = documentConfig(draft.type);
  const title = config.label;
  const secondaryDateLabel = config.dateField === 'expiry_date' ? 'Valid until' : config.dateField === 'due_date' ? 'Due date' : null;

  function update(values) { onChange({ ...draft, ...values }); }

  function updateItem(index, field, value) {
    update({ items: draft.items.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item) });
  }

  function removeItem(index) {
    if (draft.items.length === 1) return;
    update({ items: draft.items.filter((_, itemIndex) => itemIndex !== index).map((item, itemIndex) => ({ ...item, position: itemIndex })) });
  }

  function moveItem(index, direction) {
    const target = index + direction;
    if (target < 0 || target >= draft.items.length) return;
    const items = [...draft.items];
    [items[index], items[target]] = [items[target], items[index]];
    update({ items: items.map((item, itemIndex) => ({ ...item, position: itemIndex })) });
  }

  return <article className="quotation-canvas quotation-canvas--editor" aria-labelledby="document-canvas-title">
    {(message || error || totalsError) && <div className={`quotation-canvas__notice${error || totalsError ? ' quotation-canvas__notice--error' : ''}`} role={error || totalsError ? 'alert' : 'status'}>{message && <strong>{message}</strong>}{error && <strong>{error}</strong>}{totalsError && <strong>{totalsError}</strong>}</div>}
    <header className="quotation-canvas__header">
      <div className="quotation-canvas__title"><h2 id="document-canvas-title">{title}</h2><span>Draft preview</span></div>
      <div className="quotation-canvas__logo">{businessProfile?.logo_url ? <img src={businessProfile.logo_url} alt={`${businessProfile.business_name || 'Business'} logo`} /> : <span>{(businessProfile?.business_name || title.slice(0, 1)).slice(0, 1).toUpperCase()}</span>}</div>
      <div className="quotation-canvas__metadata quotation-canvas__metadata--editor">
        <label className="quotation-canvas__field"><span>Issue date *</span><input type="date" value={draft.issue_date} onChange={(event) => update({ issue_date: event.target.value })} /></label>
        <label className="quotation-canvas__field"><span>Currency *</span><input maxLength="3" value={draft.currency} onChange={(event) => update({ currency: event.target.value.toUpperCase() })} /></label>
        {config.dateField && <label className="quotation-canvas__field"><span>{secondaryDateLabel}</span><input type="date" min={draft.issue_date} value={draft[config.dateField]} onChange={(event) => update({ [config.dateField]: event.target.value })} /></label>}
      </div>
      <div className="quotation-canvas__parties quotation-canvas__parties--editor">
        <ClientSelector value={draft.client_id} selectedClient={client} onChange={(client_id, selectedClient) => (onClientChange ? onClientChange(client_id, selectedClient) : update({ client_id }))} onAddClient={onAddClient} />
        <ContactBlock label="From" name={businessProfile?.business_name} email={businessProfile?.email} phone={businessProfile?.phone} address={businessProfile?.address} />
        <ContactBlock label="Status" name="Draft" email={draft.currency} />
      </div>
    </header>
    <section className="quotation-canvas__body">
      <div className="quotation-canvas__section-heading"><h3>Line items</h3><p>Add the services or products included in this {title.toLowerCase()}.</p></div>
      <div className="quotation-canvas__items quotation-canvas__items--editor"><table><caption className="sr-only">Editable {title.toLowerCase()} line items</caption><thead><tr><th scope="col">Description</th><th scope="col">Unit cost</th><th scope="col">Qty</th><th scope="col">Amount</th><th scope="col"><span className="sr-only">Actions</span></th></tr></thead><tbody>{draft.items.map((item, index) => <tr key={item.id}><th scope="row"><input aria-label={`Item ${index + 1} description`} value={item.description} onChange={(event) => updateItem(index, 'description', event.target.value)} /></th><td><input aria-label={`Item ${index + 1} unit price`} type="number" min="0" step="0.01" value={item.unit_price} onChange={(event) => updateItem(index, 'unit_price', event.target.value)} /></td><td><input aria-label={`Item ${index + 1} quantity`} type="number" min="0.001" step="0.001" value={item.quantity} onChange={(event) => updateItem(index, 'quantity', event.target.value)} /></td><td>{formatCurrency(totals.items?.[index]?.line_total || '0.00', draft.currency)}</td><td><div className="quotation-canvas__item-actions"><button className="icon-button" type="button" aria-label={`Move item ${index + 1} up`} disabled={index === 0} onClick={() => moveItem(index, -1)}><ArrowUp size={16} aria-hidden="true" /></button><button className="icon-button" type="button" aria-label={`Move item ${index + 1} down`} disabled={index === draft.items.length - 1} onClick={() => moveItem(index, 1)}><ArrowDown size={16} aria-hidden="true" /></button><button className="icon-button" type="button" aria-label={`Remove item ${index + 1}`} disabled={draft.items.length === 1} onClick={() => removeItem(index)}><Trash2 size={16} aria-hidden="true" /></button></div></td></tr>)}</tbody></table></div>
      <button className="button button--secondary quotation-canvas__add-item" type="button" onClick={() => update({ items: [...draft.items, { ...createLineItem(), position: draft.items.length }] })}>Add line item</button>
      <section className="quotation-canvas__adjustments" aria-labelledby="document-adjustments-title"><div className="quotation-canvas__section-heading"><h3 id="document-adjustments-title">Tax and discount</h3><p>These totals are a preview. The server recalculates them when the document is saved.</p></div><div className="quotation-canvas__adjustment-fields"><label className="quotation-canvas__field"><span>Tax rate (%)</span><input type="number" min="0" step="0.001" value={draft.tax_rate} onChange={(event) => update({ tax_rate: event.target.value })} /></label><label className="quotation-canvas__field"><span>Discount type</span><select value={draft.discount_type} onChange={(event) => update({ discount_type: event.target.value, discount_value: event.target.value === 'NONE' ? '0.00' : draft.discount_value })}><option value="NONE">No discount</option><option value="FIXED">Fixed amount</option><option value="PERCENTAGE">Percentage</option></select></label><label className="quotation-canvas__field"><span>Discount value{draft.discount_type === 'PERCENTAGE' ? ' (%)' : ''}</span><input type="number" min="0" max={draft.discount_type === 'PERCENTAGE' ? '100' : undefined} step="0.01" value={draft.discount_value} disabled={draft.discount_type === 'NONE'} onChange={(event) => update({ discount_value: event.target.value })} /></label></div></section>
      <div className="quotation-canvas__bottom quotation-canvas__bottom--editor"><div className="quotation-canvas__terms quotation-canvas__terms--editor"><div className="quotation-canvas__section-heading"><h3>Notes and terms</h3></div><label className="quotation-canvas__field"><span>Notes</span><textarea value={draft.notes} onChange={(event) => update({ notes: event.target.value })} /></label>{config.hasTerms && <label className="quotation-canvas__field"><span>Terms</span><textarea value={draft.terms} onChange={(event) => update({ terms: event.target.value })} /></label>}</div><DocumentTotals totals={totals} currency={draft.currency} /></div>
    </section>
    <footer className="quotation-canvas__footer quotation-canvas__footer--editor"><span>Final totals are recalculated and stored by the server.</span><div className="document-editor__actions"><button className="button button--secondary" type="button" onClick={onAddClient}>Add client</button><button className="button" type="submit" disabled={submitting || Boolean(totalsError)}>{submitting ? 'Saving...' : 'Save preview'}</button></div></footer>
  </article>;
}
