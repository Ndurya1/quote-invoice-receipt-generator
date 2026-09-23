import { useState } from 'react';
import ConfirmDialog from '../../../components/overlays/ConfirmDialog.jsx';

export default function InvoiceReceiptConversionDialog({ open, invoice, pending = false, error = '', onCancel, onConfirm }) {
  const [issueDate, setIssueDate] = useState(invoice?.issue_date || '');
  const [validationError, setValidationError] = useState('');

  function confirm() {
    if (!issueDate) { setValidationError('Choose a receipt issue date.'); return; }
    setValidationError('');
    onConfirm({ issue_date: issueDate });
  }

  if (!open) return null;
  return <ConfirmDialog open={open} title="Create receipt from invoice?" confirmLabel="Create receipt" cancelLabel="Keep invoice" pending={pending} loadingLabel="Creating…" onCancel={onCancel} onConfirm={confirm}>
    <div className="dialog-form"><p>This will create a receipt linked to this invoice. The invoice record will remain available.</p><label className="field"><span className="field__label">Receipt issue date *</span><input type="date" value={issueDate} onChange={(event) => setIssueDate(event.target.value)} /></label>{(validationError || error) && <p className="form-error" role="alert">{validationError || error}</p>}</div>
  </ConfirmDialog>;
}
