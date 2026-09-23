import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createQuotation } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useAuth } from '../auth/useAuth.js';
import { useDataCache } from '../app/useDataCache.js';
import DocumentEditor from '../features/documents/components/DocumentEditor.jsx';
import { createDocumentDraft } from '../features/documents/documentDraft.js';
import useUnsavedDocumentChanges from '../features/documents/useUnsavedDocumentChanges.js';
import { createPreviewQuotation } from '../features/quotations/quotationPreview.js';
import { quotationPath, validateQuotationDates } from '../features/quotations/quotationData.js';
import { getPreviewClient } from '../features/clients/clientPreview.js';

export default function QuotationCreatePage() {
  const { businessProfile } = useAuth();
  const navigate = useNavigate();
  const cache = useDataCache();
  const initialDraft = useMemo(() => ({ ...createDocumentDraft({ type: 'quotation', businessProfile }), ...(isAuthPreviewEnabled ? { client_id: 'client-001' } : {}) }), [businessProfile]);
  const [draft, setDraft] = useState(initialDraft);
  const [client, setClient] = useState(() => (isAuthPreviewEnabled ? getPreviewClient('client-001') : null));
  const [state, setState] = useState({ pending: false, message: '', error: '' });
  const dirty = JSON.stringify(draft) !== JSON.stringify(initialDraft);
  useUnsavedDocumentChanges(dirty);

  async function submit(payload) {
    const dateErrors = validateQuotationDates(draft);
    if (!draft.client_id) { setState({ pending: false, message: '', error: 'Choose a client before saving the quotation.' }); return; }
    if (Object.keys(dateErrors).length) { setState({ pending: false, message: '', error: Object.values(dateErrors)[0] }); return; }
    setState({ pending: true, message: '', error: '' });
    try {
      const quotation = isAuthPreviewEnabled ? createPreviewQuotation(payload) : await createQuotation(payload);
      cache.removeByPrefix('quotations:list:');
      cache.removeByPrefix('documents:quotations:list:');
      cache.remove('dashboard:summary');
      navigate(quotationPath(quotation.id), { replace: true, state: { message: 'Quotation saved successfully.' } });
    } catch (error) {
      setState({ pending: false, message: '', error: error.message || 'The quotation could not be saved. Please try again.' });
    }
  }

  function handleClientChange(clientId, selectedClient) {
    setDraft((current) => ({ ...current, client_id: clientId }));
    setClient(selectedClient || null);
  }

  return <section className="document-page" aria-labelledby="quotation-create-title">
    <header className="page-header"><div><h1 id="quotation-create-title">New quotation</h1><p className="page-header__description">Prepare a clear proposal with live totals before saving it.</p></div></header>
    <DocumentEditor draft={draft} client={client} onChange={setDraft} onClientChange={handleClientChange} onSubmit={submit} onAddClient={() => setState((current) => ({ ...current, message: 'Add the client first from the Clients workspace, then return here to select them.' }))} submitting={state.pending} message={state.message} error={state.error} />
  </section>;
}
