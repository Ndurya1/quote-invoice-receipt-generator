import { ArrowDown, ArrowUp, Trash2 } from 'lucide-react';
import { createLineItem } from '../documentDraft.js';

export default function LineItemsEditor({ items, onChange }) {
  function update(index, field, value) {
    onChange(items.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item));
  }

  function remove(index) {
    if (items.length === 1) return;
    onChange(items.filter((_, itemIndex) => itemIndex !== index).map((item, itemIndex) => ({ ...item, position: itemIndex })));
  }

  function move(index, direction) {
    const target = index + direction;
    if (target < 0 || target >= items.length) return;
    const next = [...items];
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next.map((item, itemIndex) => ({ ...item, position: itemIndex })));
  }

  return (
    <section className="document-form-section" aria-labelledby="document-items-title">
      <div className="document-form-section__heading"><h2 id="document-items-title">Line items</h2><p>Add the services or products included in this document.</p></div>
      <div className="document-line-items">
        {items.map((item, index) => (
          <fieldset className="document-line-item" key={item.id}>
            <legend>Item {index + 1}</legend>
            <label className="field"><span className="field__label">Description *</span><input value={item.description} onChange={(event) => update(index, 'description', event.target.value)} /></label>
            <label className="field"><span className="field__label">Quantity *</span><input type="number" min="0.001" step="0.001" value={item.quantity} onChange={(event) => update(index, 'quantity', event.target.value)} /></label>
            <label className="field"><span className="field__label">Unit price *</span><input type="number" min="0" step="0.01" value={item.unit_price} onChange={(event) => update(index, 'unit_price', event.target.value)} /></label>
            <div className="document-line-item__actions"><button className="icon-button" type="button" aria-label={`Move item ${index + 1} up`} disabled={index === 0} onClick={() => move(index, -1)}><ArrowUp size={16} aria-hidden="true" /></button><button className="icon-button" type="button" aria-label={`Move item ${index + 1} down`} disabled={index === items.length - 1} onClick={() => move(index, 1)}><ArrowDown size={16} aria-hidden="true" /></button><button className="icon-button" type="button" aria-label={`Remove item ${index + 1}`} disabled={items.length === 1} onClick={() => remove(index)}><Trash2 size={16} aria-hidden="true" /></button></div>
          </fieldset>
        ))}
      </div>
      <button className="button button--secondary" type="button" onClick={() => onChange([...items, { ...createLineItem(), position: items.length }])}>Add line item</button>
    </section>
  );
}
