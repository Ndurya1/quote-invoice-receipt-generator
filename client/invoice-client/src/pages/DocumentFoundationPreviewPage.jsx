import { useMemo, useState } from 'react';
import { useAuth } from '../auth/useAuth.js';
import { getPreviewClient } from '../features/clients/clientPreview.js';
import { createDocumentDraft } from '../features/documents/documentDraft.js';
import DocumentEditor from '../features/documents/components/DocumentEditor.jsx';
import useUnsavedDocumentChanges from '../features/documents/useUnsavedDocumentChanges.js';

const labels = { quotation: 'quotation', invoice: 'invoice', receipt: 'receipt' };

export default function DocumentFoundationPreviewPage({ type }) {
  const { businessProfile } = useAuth();
  const initialDraft = useMemo(() => ({ ...createDocumentDraft({ type, businessProfile }), client_id: 'client-001' }), [businessProfile, type]);
  const [draft, setDraft] = useState(initialDraft);
  const [client, setClient] = useState(() => getPreviewClient('client-001'));
  const [message, setMessage] = useState('');
  const dirty = JSON.stringify(draft) !== JSON.stringify(initialDraft);
  useUnsavedDocumentChanges(dirty);

  function handleChange(nextDraft) { setMessage(''); setDraft(nextDraft); }
  function handleSubmit() { setMessage('Foundation preview only — no document was saved.'); }
  function handleClientChange(clientId, selectedClient) {
    setDraft((current) => ({ ...current, client_id: clientId }));
    setClient(selectedClient || null);
  }

  return <div className="document-foundation-page">
    <header className="page-header document-foundation-header"><div><h1>New {labels[type]}</h1><p>Developer preview of the shared document editor. Server recalculation remains authoritative.</p></div><span className="preview-badge">Developer preview</span></header>
    <DocumentEditor draft={draft} client={client} onChange={handleChange} onClientChange={handleClientChange} onSubmit={handleSubmit} onAddClient={() => setMessage('Inline client creation will connect to the client form in the next document phase.')} message={message} />
  </div>;
}
