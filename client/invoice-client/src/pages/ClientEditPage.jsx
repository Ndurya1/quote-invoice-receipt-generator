import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { updateClient } from '../api/clientsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useDataCache } from '../app/useDataCache.js';
import { clientDetailPath, clientErrorMessage, clientFieldErrors, clientFormValues, serializeClientPatch } from '../features/clients/clientData.js';
import { updatePreviewClient } from '../features/clients/clientPreview.js';
import { useClient } from '../features/clients/useClients.js';
import { useUnsavedChanges } from '../features/clients/useUnsavedChanges.js';
import { ClientsError, ClientsLoading } from '../features/clients/components/ClientListFeedback.jsx';
import ClientForm from '../features/clients/components/ClientForm.jsx';

export default function ClientEditPage() {
  const { clientId } = useParams();
  const navigate = useNavigate();
  const cache = useDataCache();
  const { status, data: client, error, retry } = useClient(clientId);
  const [state, setState] = useState({ submitting: false, error: '', fieldErrors: {} });
  const [dirty, setDirty] = useState(false);
  useUnsavedChanges(dirty);

  async function submit(values) {
    setState({ submitting: true, error: '', fieldErrors: {} });
    try {
      const payload = serializeClientPatch(values, client);
      const updated = Object.keys(payload).length === 0
        ? client
        : isAuthPreviewEnabled ? updatePreviewClient(clientId, payload) : await updateClient(clientId, payload);
      cache.set(`clients:detail:${clientId}`, updated);
      cache.removeByPrefix('clients:list:');
      setDirty(false);
      navigate(clientDetailPath(clientId));
    } catch (updateError) {
      setState({ submitting: false, error: clientErrorMessage(updateError), fieldErrors: clientFieldErrors(updateError) });
    }
  }

  if (status === 'loading') return <ClientsLoading />;
  if (status === 'error') return <ClientsError message={clientErrorMessage(error)} onRetry={retry} />;

  return (
    <section className="client-form-page" aria-labelledby="client-edit-title">
      <header className="page-header"><div><p className="eyebrow">Clients</p><h1 id="client-edit-title">Edit {client.name}</h1><p className="page-header__description">Update the reusable details shown on future documents.</p></div></header>
      <div className="client-form-card"><ClientForm initialValues={clientFormValues(client)} submitLabel="Save changes" cancelTo={clientDetailPath(client.id)} onSubmit={submit} submitting={state.submitting} serverError={state.error} serverErrors={state.fieldErrors} onDirtyChange={setDirty} /></div>
    </section>
  );
}
