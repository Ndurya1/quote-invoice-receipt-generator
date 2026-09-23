import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createClient } from '../api/clientsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useDataCache } from '../app/useDataCache.js';
import { clientDetailPath, clientFieldErrors, clientErrorMessage, clientFormValues, serializeClientCreate } from '../features/clients/clientData.js';
import { createPreviewClient } from '../features/clients/clientPreview.js';
import ClientForm from '../features/clients/components/ClientForm.jsx';

export default function ClientCreatePage() {
  const navigate = useNavigate();
  const cache = useDataCache();
  const [state, setState] = useState({ submitting: false, error: '', fieldErrors: {} });

  async function submit(values) {
    setState({ submitting: true, error: '', fieldErrors: {} });
    try {
      const payload = serializeClientCreate(values);
      const client = isAuthPreviewEnabled ? createPreviewClient(payload) : await createClient(payload);
      cache.set(`clients:detail:${client.id}`, client);
      cache.removeByPrefix('clients:list:');
      navigate(`${clientDetailPath(client.id)}?created=1`);
    } catch (error) {
      setState({ submitting: false, error: clientErrorMessage(error), fieldErrors: clientFieldErrors(error) });
    }
  }

  return (
    <section className="client-form-page" aria-labelledby="client-create-title">
      <header className="page-header"><div><p className="eyebrow">Clients</p><h1 id="client-create-title">Add client</h1><p className="page-header__description">Save contact details once and reuse them across your documents.</p></div></header>
      <div className="client-form-card"><ClientForm initialValues={clientFormValues()} submitLabel="Save client" onSubmit={submit} submitting={state.submitting} serverError={state.error} serverErrors={state.fieldErrors} /></div>
    </section>
  );
}
