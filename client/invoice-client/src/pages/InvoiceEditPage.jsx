import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { updateInvoice } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useDataCache } from '../app/useDataCache.js';
import { useClient } from '../features/clients/useClients.js';
import DocumentEditor from '../features/documents/components/DocumentEditor.jsx';
import { hydrateDocumentDraft, serializeDocumentPayload } from '../features/documents/documentDraft.js';
import useUnsavedDocumentChanges from '../features/documents/useUnsavedDocumentChanges.js';
import { invoiceErrorMessage, invoicePath, isInvoiceEditable, validateInvoiceDates } from '../features/invoices/invoiceData.js';
import { updatePreviewInvoice } from '../features/invoices/invoicePreview.js';
import { useInvoice } from '../features/invoices/useInvoices.js';

export default function InvoiceEditPage() {
  const { invoiceId } = useParams();
  const invoiceState = useInvoice(invoiceId);
  if (invoiceState.status === 'loading') return <div className="document-feedback">Loading invoice…</div>;
  if (invoiceState.status === 'error') return <div className="document-feedback document-feedback--error"><strong>{invoiceErrorMessage(invoiceState.error)}</strong><button className="button button--secondary" type="button" onClick={invoiceState.retry}>Try again</button></div>;
  return <InvoiceEditLoaded invoice={invoiceState.data} />;
}

function InvoiceEditLoaded({ invoice }) {
  const navigate = useNavigate();
  const cache = useDataCache();
  const { data: client } = useClient(invoice.client_id);
  const initialDraft = useMemo(() => hydrateDocumentDraft(invoice, 'invoice'), [invoice]);
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

  if (!isInvoiceEditable(invoice)) return <section className="document-feedback document-feedback--error"><strong>This invoice is no longer editable.</strong><p>Only direct, unlinked draft invoices can be changed.</p><Link className="button button--secondary" to={invoicePath(invoice.id)}>Back to invoice</Link></section>;

  async function submit() {
    const dateErrors = validateInvoiceDates(draft);
    if (Object.keys(dateErrors).length) { setState({ pending: false, error: Object.values(dateErrors)[0] }); return; }
    setState({ pending: true, error: '' });
    try {
      const payload = serializeDocumentPayload(draft, 'invoice');
      const updated = isAuthPreviewEnabled ? updatePreviewInvoice(invoice.id, payload) : await updateInvoice(invoice.id, payload);
      cache.remove(`invoices:detail:${invoice.id}`);
      cache.removeByPrefix('invoices:list:');
      navigate(invoicePath(updated.id), { replace: true, state: { message: 'Invoice updated successfully.' } });
    } catch (error) {
      if (error.status === 409) {
        cache.remove(`invoices:detail:${invoice.id}`);
        navigate(invoicePath(invoice.id), { replace: true, state: { message: 'This invoice changed before it could be saved. Review the refreshed invoice.' } });
        return;
      }
      setState({ pending: false, error: invoiceErrorMessage(error) });
    }
  }

  return <section className="document-page" aria-labelledby="invoice-edit-title">
    <header className="page-header"><div><h1 id="invoice-edit-title">Edit {invoice.invoice_number}</h1><p className="page-header__description">Update this direct draft before sending it to your client.</p></div></header>
    <DocumentEditor draft={draft} client={selectedClient} onChange={setDraft} onClientChange={(clientId, nextClient) => { setDraft((current) => ({ ...current, client_id: clientId })); setSelectedClient(nextClient || null); }} onSubmit={submit} onAddClient={() => setState((current) => ({ ...current, error: 'Add or update clients from the Clients workspace.' }))} submitting={state.pending} error={state.error} />
  </section>;
}
