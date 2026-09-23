import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { clientDetailPath, clientListDate, clientListSearchParams, clientListParams, readClientListQuery } from '../features/clients/clientData.js';
import { useClientsList } from '../features/clients/useClients.js';
import { ClientsError, ClientsLoading } from '../features/clients/components/ClientListFeedback.jsx';

const sortOptions = [
  { value: '-created_at', label: 'Recently added' },
  { value: 'name', label: 'Name A–Z' },
  { value: '-name', label: 'Name Z–A' },
];

export default function ClientsPage() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryString = searchParams.toString();
  const query = useMemo(() => readClientListQuery(new URLSearchParams(queryString)), [queryString]);
  const requestQuery = useMemo(() => clientListParams(query), [query]);
  const [search, setSearch] = useState(query.search);
  const { status, data, error, retry } = useClientsList(requestQuery);
  const totalPages = data ? Math.max(1, Math.ceil(data.meta.total / data.meta.page_size)) : 1;

  useEffect(() => {
    // Keep the input aligned with browser back/forward URL changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSearch(query.search);
  }, [query.search]);

  useEffect(() => {
    if (search === query.search) return undefined;
    const timer = setTimeout(() => {
      setSearchParams(clientListSearchParams({ ...query, search, page: 1 }));
    }, 300);
    return () => clearTimeout(timer);
  }, [query, search, setSearchParams]);

  function updateQuery(values) {
    setSearchParams(clientListSearchParams({ ...query, ...values }));
  }

  function clearFilters() {
    setSearch('');
    setSearchParams(clientListSearchParams({ page: 1, page_size: query.page_size, search: '', sort: '-created_at' }));
  }

  return (
    <section className="clients-page" aria-labelledby="clients-title">
      <header className="page-header clients-header">
        <div><h1 id="clients-title">Clients</h1><p className="page-header__description">Keep reusable client details ready for every quotation, invoice, and receipt.</p></div>
        <Link className="button" to="/clients/new">New client</Link>
      </header>

      {location.state?.message && <div className="alert alert--success" role="status">{location.state.message}</div>}

      <section className="clients-workspace" aria-label="Client list">
        <div className="clients-toolbar">
          <label className="clients-search field">
            <span className="field__label">Search clients</span>
            <input type="search" value={search} placeholder="Search by name, email, or phone" onChange={(event) => setSearch(event.target.value)} />
          </label>
          <label className="clients-sort field">
            <span className="field__label">Sort</span>
            <select value={query.sort} onChange={(event) => updateQuery({ sort: event.target.value, page: 1 })}>
              {sortOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          {(query.search || query.sort !== '-created_at') && <button className="button button--secondary clients-clear" type="button" onClick={clearFilters}>Clear filters</button>}
        </div>

        {status === 'loading' && <ClientsLoading />}
        {status === 'error' && <ClientsError message={error?.message} onRetry={retry} />}
        {status === 'success' && data.data.length === 0 && (
          <div className="empty-state clients-empty">
            <h2>{query.search ? 'No matching clients' : 'No clients yet'}</h2>
            <p>{query.search ? 'Try a different search or clear the filter.' : 'Add your first client so their details are ready when you create a document.'}</p>
            {query.search ? <button className="button button--secondary" type="button" onClick={clearFilters}>Clear search</button> : <Link className="button" to="/clients/new">Add client</Link>}
          </div>
        )}
        {status === 'success' && data.data.length > 0 && (
          <>
            <div className="clients-table-wrap">
              <table className="clients-table">
                <caption className="sr-only">Client records</caption>
                <thead><tr><th scope="col">Client</th><th scope="col">Email</th><th scope="col">Phone</th><th scope="col">Added</th><th scope="col"><span className="sr-only">Actions</span></th></tr></thead>
                <tbody>{data.data.map((client) => (
                  <tr key={client.id}>
                    <th scope="row"><Link className="client-table__name" to={clientDetailPath(client.id)}>{client.name}</Link></th>
                    <td data-label="Email">{client.email || '—'}</td>
                    <td data-label="Phone">{client.phone || '—'}</td>
                    <td data-label="Added">{clientListDate(client.created_at)}</td>
                    <td data-label="Actions"><Link className="text-link" to={clientDetailPath(client.id)}>Open</Link></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            <div className="clients-pagination" aria-label="Client pagination">
              <span>{data.meta.total} {data.meta.total === 1 ? 'client' : 'clients'} · Page {query.page} of {totalPages}</span>
              <div><button className="button button--secondary" type="button" disabled={query.page <= 1} onClick={() => updateQuery({ page: query.page - 1 })}>Previous</button><button className="button button--secondary" type="button" disabled={query.page >= totalPages} onClick={() => updateQuery({ page: query.page + 1 })}>Next</button></div>
            </div>
          </>
        )}
      </section>
    </section>
  );
}
