import { useState } from 'react';
import ConfirmDialog from '../../../components/overlays/ConfirmDialog.jsx';

export default function QuotationConversionDialog({ open, quotation, pending = false, error = '', onCancel, onConfirm }) {
  const [values, setValues] = useState({ issue_date: quotation?.issue_date || '', due_date: '' });
  const [validationError, setValidationError] = useState('');

  function confirm() {
    if (!values.issue_date) { setValidationError('Choose an invoice issue date.'); return; }
    if (values.due_date && values.due_date < values.issue_date) { setValidationError('Due date cannot precede issue date.'); return; }
    setValidationError('');
    onConfirm({ ...values, due_date: values.due_date || null });
  }

  if (!open) return null;
  return <ConfirmDialog open={open} title="Create invoice from quotation?" confirmLabel="Create invoice" cancelLabel="Keep quotation" pending={pending} loadingLabel="Creating…" onCancel={onCancel} onConfirm={confirm}>
    <div className="dialog-form"><p>This will mark the quotation as converted and create a draft invoice with the same items and totals.</p><label className="field"><span className="field__label">Invoice issue date *</span><input type="date" value={values.issue_date} onChange={(event) => setValues((current) => ({ ...current, issue_date: event.target.value }))} /></label><label className="field"><span className="field__label">Due date</span><input type="date" min={values.issue_date} value={values.due_date} onChange={(event) => setValues((current) => ({ ...current, due_date: event.target.value }))} /></label>{(validationError || error) && <p className="form-error" role="alert">{validationError || error}</p>}</div>
  </ConfirmDialog>;
}
