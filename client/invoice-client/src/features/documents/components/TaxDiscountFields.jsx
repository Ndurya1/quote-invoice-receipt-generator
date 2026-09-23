export default function TaxDiscountFields({ draft, onChange }) {
  return (
    <section className="document-form-section" aria-labelledby="document-adjustments-title">
      <div className="document-form-section__heading"><h2 id="document-adjustments-title">Tax and discount</h2><p>These totals are a preview. The server recalculates them when the document is saved.</p></div>
      <div className="document-adjustment-grid">
        <label className="field"><span className="field__label">Tax rate (%)</span><input type="number" min="0" step="0.001" value={draft.tax_rate} onChange={(event) => onChange({ tax_rate: event.target.value })} /></label>
        <label className="field"><span className="field__label">Discount type</span><select value={draft.discount_type} onChange={(event) => onChange({ discount_type: event.target.value, discount_value: event.target.value === 'NONE' ? '0.00' : draft.discount_value })}><option value="NONE">No discount</option><option value="FIXED">Fixed amount</option><option value="PERCENTAGE">Percentage</option></select></label>
        <label className="field"><span className="field__label">Discount value{draft.discount_type === 'PERCENTAGE' ? ' (%)' : ''}</span><input type="number" min="0" max={draft.discount_type === 'PERCENTAGE' ? '100' : undefined} step="0.01" value={draft.discount_value} disabled={draft.discount_type === 'NONE'} onChange={(event) => onChange({ discount_value: event.target.value })} /></label>
      </div>
    </section>
  );
}
