import { useMemo, useState } from 'react';
import { useClientsList } from '../../clients/useClients.js';

export default function ClientSelector({ value, selectedClient, onChange, onAddClient }) {
  const [search, setSearch] = useState('');
  const query = useMemo(() => ({ page: 1, page_size: 8, search, sort: 'name' }), [search]);
  const { status, data } = useClientsList(query);
  const options = data?.data || [];

  return (
    <div className="document-client-selector field">
      <span className="field__label">Client *</span>
      {selectedClient && <div className="document-client-selector__selected"><strong>{selectedClient.name}</strong><button className="text-button" type="button" onClick={() => onChange('')}>Change</button></div>}
      {!selectedClient && <>
        <input type="search" value={search} placeholder="Search clients" onChange={(event) => setSearch(event.target.value)} aria-label="Search clients" />
        {status === 'loading' && <span className="field__helper">Loading clients…</span>}
        {status === 'success' && <div className="document-client-selector__options" role="listbox" aria-label="Client results">
          {options.map((client) => <button key={client.id} type="button" role="option" aria-selected={client.id === value} onClick={() => onChange(client.id, client)}>{client.name}<small>{client.email || client.phone || 'No contact details'}</small></button>)}
          {options.length === 0 && <span className="field__helper">No matching clients.</span>}
        </div>}
        <button className="text-button document-client-selector__add" type="button" onClick={onAddClient}>Add client</button>
      </>}
    </div>
  );
}
