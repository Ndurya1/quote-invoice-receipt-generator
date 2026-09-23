import { useMemo } from 'react';
import { useAuth } from '../../../auth/useAuth.js';
import DocumentCanvasEditor from './DocumentCanvasEditor.jsx';
import { calculateDocumentTotals } from '../documentCalculations.js';
import { serializeDocumentPayload } from '../documentDraft.js';

export default function DocumentEditor({ draft, client, onChange, onSubmit, onAddClient, onClientChange, submitting = false, message = '', error = '' }) {
  const { businessProfile } = useAuth();
  const totals = useMemo(() => {
    try {
      return { ...calculateDocumentTotals({ items: draft.items, taxRate: draft.tax_rate, discountType: draft.discount_type, discountValue: draft.discount_value }), error: '' };
    } catch (calculationError) {
      return { subtotal: '0.00', taxAmount: '0.00', discountAmount: '0.00', total: '0.00', error: calculationError.message };
    }
  }, [draft]);

  function submit(event) {
    event.preventDefault();
    onSubmit(serializeDocumentPayload(draft, draft.type));
  }

  return <form className="document-editor" onSubmit={submit}><DocumentCanvasEditor draft={draft} client={client} businessProfile={businessProfile} totals={totals} onChange={onChange} onAddClient={onAddClient} onClientChange={onClientChange} message={message} error={error} totalsError={totals.error} submitting={submitting} /></form>;
}
