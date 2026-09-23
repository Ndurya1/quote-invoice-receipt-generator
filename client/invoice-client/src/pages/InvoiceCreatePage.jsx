import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createInvoice } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useAuth } from '../auth/useAuth.js';
import { useDataCache } from '../app/useDataCache.js';
import DocumentEditor from '../features/documents/components/DocumentEditor.jsx';
import { createDocumentDraft } from '../features/documents/documentDraft.js';
import useUnsavedDocumentChanges from '../features/documents/useUnsavedDocumentChanges.js';
import { getPreviewClient } from '../features/clients/clientPreview.js';
import { createPreviewInvoice } from '../features/invoices/invoicePreview.js';
import { invoicePath, validateInvoiceDates } from '../features/invoices/invoiceData.js';

export default function InvoiceCreatePage() {
  const { businessProfile } = useAuth();
  const navigate = useNavigate();
  const cache = useDataCache();
  const initialDraft = useMemo(() => ({ ...createDocumentDraft({ type: 'invoice', businessProfile }), ...(isAuthPreviewEnabled ? { client_id: 'client-001' } : {}) }), [businessProfile]);
  const [draft, setDraft] = useState(initialDraft);
  const [client, setClient] = useState(() => (isAuthPreviewEnabled ? getPreviewClient('client-001') : null));
  const [state, setState] = useState({ pending: false, message: '', error: '' });
  const dirty = JSON.stringify(draft) !== JSON.stringify(initialDraft);
  useUnsavedDocumentChanges(dirty);

  async function submit(payload) {
    const dateErrors = validateInvoiceDates(draft);
    if (!draft.client_id) { setState({ pending: false, message: '', error: 'Choose a client before saving the invoice.' }); return; }
    if (Object.keys(dateErrors).length) { setState({ pending: false, message: '', error: Object.values(dateErrors)[0] }); return; }
    setState({ pending: true, message: '', error: '' });
    try {
      const invoice = isAuthPreviewEnabled ? createPreviewInvoice(payload) : await createInvoice(payload);
      cache.removeByPrefix('invoices:list:');
      cache.removeByPrefix('documents:invoices:list:');
      cache.remove('dashboard:summary');
      navigate(invoicePath(invoice.id), { replace: true, state: { message: 'Invoice saved successfully.' } });
    } catch (error) {
      setState({ pending: false, message: '', error: error.message || 'The invoice could not be saved. Please try again.' });
    }
  }

  function handleClientChange(clientId, selectedClient) {
    setDraft((current) => ({ ...current, client_id: clientId }));
    setClient(selectedClient || null);
  }

  return <section className="document-page" aria-labelledby="invoice-create-title">
    <header className="page-header"><div><h1 id="invoice-create-title">New invoice</h1><p className="page-header__description">Prepare a clear invoice with live totals before saving it.</p></div></header>
    <DocumentEditor draft={draft} client={client} onChange={setDraft} onClientChange={handleClientChange} onSubmit={submit} onAddClient={() => setState((current) => ({ ...current, message: 'Add the client first from the Clients workspace, then return here to select them.' }))} submitting={state.pending} message={state.message} error={state.error} />
  </section>;
}
