import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { updateReceipt } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useDataCache } from '../app/useDataCache.js';
import { useClient } from '../features/clients/useClients.js';
import DocumentEditor from '../features/documents/components/DocumentEditor.jsx';
import { hydrateDocumentDraft, serializeDocumentPayload } from '../features/documents/documentDraft.js';
import useUnsavedDocumentChanges from '../features/documents/useUnsavedDocumentChanges.js';
import { updatePreviewReceipt } from '../features/receipts/receiptPreview.js';
import { isReceiptEditable, receiptErrorMessage, receiptPath, validateReceiptDates } from '../features/receipts/receiptData.js';
import { useReceipt } from '../features/receipts/useReceipts.js';

export default function ReceiptEditPage() {
  const { receiptId } = useParams();
  const receiptState = useReceipt(receiptId);
  if (receiptState.status === 'loading') return <div className="document-feedback">Loading receipt...</div>;
  if (receiptState.status === 'error') return <div className="document-feedback document-feedback--error"><strong>{receiptErrorMessage(receiptState.error)}</strong><button className="button button--secondary" type="button" onClick={receiptState.retry}>Try again</button></div>;
  return <ReceiptEditLoaded receipt={receiptState.data} />;
}

function ReceiptEditLoaded({ receipt }) {
  const navigate = useNavigate();
  const cache = useDataCache();
  const { data: client } = useClient(receipt.client_id);
  const initialDraft = useMemo(() => hydrateDocumentDraft(receipt, 'receipt'), [receipt]);
  const [draft, setDraft] = useState(initialDraft);
  const [selectedClient, setSelectedClient] = useState(client || null);
  const [state, setState] = useState({ pending: false, error: '' });
  const dirty = JSON.stringify(draft) !== JSON.stringify(initialDraft);
  useUnsavedDocumentChanges(dirty);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDraft(initialDraft);
  }, [initialDraft]);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (client) setSelectedClient(client);
  }, [client]);

  if (!isReceiptEditable(receipt)) return <section className="document-feedback document-feedback--error"><strong>This receipt is no longer editable.</strong><p>Receipts created from invoices preserve the invoice history and cannot be changed.</p><Link className="button button--secondary" to={receiptPath(receipt.id)}>Back to receipt</Link></section>;

  async function submit() {
    const dateErrors = validateReceiptDates(draft);
    if (Object.keys(dateErrors).length) { setState({ pending: false, error: Object.values(dateErrors)[0] }); return; }
    setState({ pending: true, error: '' });
    try {
      const payload = serializeDocumentPayload(draft, 'receipt');
      const updated = isAuthPreviewEnabled ? updatePreviewReceipt(receipt.id, payload) : await updateReceipt(receipt.id, payload);
      cache.remove(`receipts:detail:${receipt.id}`);
      cache.removeByPrefix('receipts:list:');
      cache.removeByPrefix('documents:receipts:list:');
      navigate(receiptPath(updated.id), { replace: true, state: { message: 'Receipt updated successfully.' } });
    } catch (error) {
      setState({ pending: false, error: receiptErrorMessage(error) });
    }
  }

  return <section className="document-page" aria-labelledby="receipt-edit-title"><header className="page-header"><div><h1 id="receipt-edit-title">Edit {receipt.receipt_number}</h1><p className="page-header__description">Update this direct receipt before downloading it.</p></div></header><DocumentEditor draft={draft} client={selectedClient} onChange={setDraft} onClientChange={(clientId, nextClient) => { setDraft((current) => ({ ...current, client_id: clientId })); setSelectedClient(nextClient || null); }} onSubmit={submit} onAddClient={() => setState((current) => ({ ...current, error: 'Add or update clients from the Clients workspace.' }))} submitting={state.pending} error={state.error} /></section>;
}
