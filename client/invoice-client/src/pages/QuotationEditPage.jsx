import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { updateQuotation } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useDataCache } from '../app/useDataCache.js';
import { useClient } from '../features/clients/useClients.js';
import DocumentEditor from '../features/documents/components/DocumentEditor.jsx';
import { hydrateDocumentDraft, serializeDocumentPayload } from '../features/documents/documentDraft.js';
import useUnsavedDocumentChanges from '../features/documents/useUnsavedDocumentChanges.js';
import { updatePreviewQuotation } from '../features/quotations/quotationPreview.js';
import { isQuotationEditable, quotationErrorMessage, quotationPath, validateQuotationDates } from '../features/quotations/quotationData.js';
import { useQuotation } from '../features/quotations/useQuotations.js';

export default function QuotationEditPage() {
  const { quoteId } = useParams();
  const quotationState = useQuotation(quoteId);
  if (quotationState.status === 'loading') return <div className="document-feedback">Loading quotation…</div>;
  if (quotationState.status === 'error') return <div className="document-feedback document-feedback--error"><strong>{quotationErrorMessage(quotationState.error)}</strong><button className="button button--secondary" type="button" onClick={quotationState.retry}>Try again</button></div>;
  return <QuotationEditLoaded quotation={quotationState.data} />;
}

function QuotationEditLoaded({ quotation }) {
  const navigate = useNavigate();
  const cache = useDataCache();
  const { data: client } = useClient(quotation.client_id);
  const initialDraft = useMemo(() => hydrateDocumentDraft(quotation, 'quotation'), [quotation]);
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

  if (!isQuotationEditable(quotation)) return <section className="document-feedback document-feedback--error"><strong>This quotation is no longer editable.</strong><p>Only unlinked draft quotations can be changed.</p><Link className="button button--secondary" to={quotationPath(quotation.id)}>Back to quotation</Link></section>;

  async function submit() {
    const dateErrors = validateQuotationDates(draft);
    if (Object.keys(dateErrors).length) { setState({ pending: false, error: Object.values(dateErrors)[0] }); return; }
    setState({ pending: true, error: '' });
    try {
      const payload = serializeDocumentPayload(draft, 'quotation');
      const updated = isAuthPreviewEnabled ? updatePreviewQuotation(quotation.id, payload) : await updateQuotation(quotation.id, payload);
      cache.remove(`quotations:detail:${quotation.id}`);
      cache.removeByPrefix('quotations:list:');
      cache.removeByPrefix('documents:quotations:list:');
      navigate(quotationPath(updated.id), { replace: true, state: { message: 'Quotation updated successfully.' } });
    } catch (error) {
      if (error.status === 409) {
        cache.remove(`quotations:detail:${quotation.id}`);
        navigate(quotationPath(quotation.id), { replace: true, state: { message: 'This quotation changed before it could be saved. Review the refreshed quotation.' } });
        return;
      }
      setState({ pending: false, error: quotationErrorMessage(error) });
    }
  }

  return <section className="document-page" aria-labelledby="quotation-edit-title">
    <header className="page-header"><div><h1 id="quotation-edit-title">Edit {quotation.quote_number}</h1><p className="page-header__description">Update this draft before sending it to your client.</p></div></header>
    <DocumentEditor draft={draft} client={selectedClient} onChange={setDraft} onClientChange={(clientId, nextClient) => { setDraft((current) => ({ ...current, client_id: clientId })); setSelectedClient(nextClient || null); }} onSubmit={submit} onAddClient={() => setState((current) => ({ ...current, error: 'Add or update clients from the Clients workspace.' }))} submitting={state.pending} error={state.error} />
  </section>;
}
