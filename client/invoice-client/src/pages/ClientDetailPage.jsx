import { useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { deleteClient } from '../api/clientsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useDataCache } from '../app/useDataCache.js';
import { clientDocumentsPath, clientEditPath, clientErrorMessage } from '../features/clients/clientData.js';
import { deletePreviewClient } from '../features/clients/clientPreview.js';
import { useClient } from '../features/clients/useClients.js';
import { ClientsError, ClientsLoading } from '../features/clients/components/ClientListFeedback.jsx';
import ConfirmDialog from '../components/overlays/ConfirmDialog.jsx';

export default function ClientDetailPage() {
  const { clientId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const cache = useDataCache();
  const { status, data: client, error, retry } = useClient(clientId);
  const [deleteState, setDeleteState] = useState({ open: false, pending: false, error: '' });
  const created = new URLSearchParams(location.search).get('created') === '1';

  async function confirmDelete() {
    setDeleteState({ open: true, pending: true, error: '' });
    try {
      if (isAuthPreviewEnabled) await Promise.resolve(deletePreviewClient(clientId));
      else await deleteClient(clientId);
      cache.remove(`clients:detail:${clientId}`);
      cache.removeByPrefix('clients:list:');
      navigate('/clients', { replace: true, state: { message: `${client.name} was deleted.` } });
    } catch (deleteError) {
      setDeleteState({ open: true, pending: false, error: clientErrorMessage(deleteError) });
    }
  }

  if (status === 'loading') return <ClientsLoading />;
  if (status === 'error') return <ClientsError message={clientErrorMessage(error)} onRetry={retry} />;

  return (
    <section className="client-detail-page" aria-labelledby="client-detail-title">
      <header className="page-header client-detail-header">
        <div><p className="eyebrow">Client record</p><h1 id="client-detail-title">{client.name}</h1><p className="page-header__description">Reusable contact details for document creation.</p></div>
        <div className="page-header__actions"><Link className="button button--secondary" to={clientEditPath(client.id)}>Edit client</Link><button className="button button--danger" type="button" onClick={() => setDeleteState({ open: true, pending: false, error: '' })}>Delete</button></div>
      </header>
      {created && <div className="alert alert--success" role="status">Client saved successfully.</div>}
      {deleteState.error && <div className="form-error" role="alert">{deleteState.error}</div>}
      <div className="client-detail-grid">
        <section className="client-detail-card" aria-labelledby="contact-details-title"><h2 id="contact-details-title">Contact details</h2><dl><div><dt>Name</dt><dd>{client.name}</dd></div><div><dt>Email</dt><dd>{client.email || 'Not provided'}</dd></div><div><dt>Phone</dt><dd>{client.phone || 'Not provided'}</dd></div><div><dt>Address</dt><dd>{client.address || 'Not provided'}</dd></div></dl></section>
        <section className="client-detail-card" aria-labelledby="client-documents-title"><h2 id="client-documents-title">Documents</h2><p>Open the document workspace filtered to this client.</p><div className="client-document-links"><Link className="button button--secondary" to={clientDocumentsPath('quotations', client.id)}>Quotations</Link><Link className="button button--secondary" to={clientDocumentsPath('invoices', client.id)}>Invoices</Link><Link className="button button--secondary" to={clientDocumentsPath('receipts', client.id)}>Receipts</Link></div></section>
      </div>
      <ConfirmDialog open={deleteState.open} title={`Delete ${client.name}?`} cancelLabel="Keep client" destructive onCancel={() => setDeleteState({ open: false, pending: false, error: '' })} onConfirm={confirmDelete} pending={deleteState.pending}>
        <p>Only clients with no document references can be deleted. Existing document history is never removed.</p>
      </ConfirmDialog>
    </section>
  );
}
