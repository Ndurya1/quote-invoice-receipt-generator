import { useEffect, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import CreateDocumentMenu from '../features/dashboard/components/CreateDocumentMenu.jsx';
import { useClientsList } from '../features/clients/useClients.js';
import EmptyState from '../components/feedback/EmptyState.jsx';
import LoadingState from '../components/feedback/LoadingState.jsx';
import RetryState from '../components/feedback/RetryState.jsx';
import { useDocuments } from '../features/documents/useDocuments.js';
import { canEditDocument, documentDetailPath, documentEditPath, documentFiltersSearchParams, documentListConfig, documentListTypes, formatDocumentRow, readDocumentFilters } from '../features/documents/documentListData.js';

function hasActiveFilters(filters) {
  return Boolean(filters.search || filters.client_id || filters.status || filters.sort !== '-created_at');
}

export default function DocumentsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const searchKey = searchParams.toString();
  const filters = useMemo(() => readDocumentFilters(new URLSearchParams(searchKey)), [searchKey]);
  const config = documentListConfig(filters.type);
  const documentState = useDocuments(filters);
  const clientsState = useClientsList({ page: 1, page_size: 100, search: '', sort: 'name' });
  const clientMap = useMemo(() => new Map((clientsState.data?.data || []).map((client) => [client.id, client])), [clientsState.data]);
  const documents = documentState.data?.data || [];
  const meta = documentState.data?.meta || { page: filters.page, page_size: filters.page_size, total: 0 };
  const totalPages = Math.max(1, Math.ceil(meta.total / meta.page_size));

  useEffect(() => {
    if (documentState.status === 'success' && meta.total > 0 && filters.page > totalPages) {
      updateUrl({ page: totalPages }, false);
    }
    // updateUrl intentionally follows the URL-backed filter state for this guard.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentState.status, filters.page, meta.total, totalPages]);

  function updateUrl(changes, resetPage = true) {
    const next = { ...filters, ...changes, page: resetPage ? 1 : changes.page ?? filters.page };
    setSearchParams(documentFiltersSearchParams(next), { replace: true });
  }

  function clearFilters() {
    updateUrl({ search: '', client_id: '', status: '', sort: '-created_at' });
  }

  return <section className="documents-page" aria-labelledby="documents-title">
    <header className="page-header documents-header"><div><h1 id="documents-title">Documents</h1><p className="page-header__description">Find every quotation, invoice, and receipt in one workspace.</p></div><div className="page-header__actions"><CreateDocumentMenu /></div></header>
    <nav className="documents-tabs" aria-label="Document types">{documentListTypes.map((type) => <button key={type} className={`documents-tab${filters.type === type ? ' is-active' : ''}`} type="button" aria-current={filters.type === type ? 'page' : undefined} onClick={() => updateUrl({ type, status: '', sort: '-created_at' })}>{documentListConfig(type).label}</button>)}</nav>
    <div className="documents-workspace">
      <div className="documents-toolbar"><label className="field"><span className="field__label">Search {config.label.toLowerCase()}</span><input type="search" value={filters.search} placeholder={`Search ${config.singular} number or notes`} onChange={(event) => updateUrl({ search: event.target.value })} /></label><label className="field"><span className="field__label">Client</span><select value={filters.client_id} onChange={(event) => updateUrl({ client_id: event.target.value })}><option value="">All clients</option>{(clientsState.data?.data || []).map((client) => <option key={client.id} value={client.id}>{client.name}</option>)}</select></label>{config.statuses.length > 0 && <label className="field"><span className="field__label">Status</span><select value={filters.status} onChange={(event) => updateUrl({ status: event.target.value })}><option value="">All statuses</option>{config.statuses.map((status) => <option key={status} value={status}>{status[0] + status.slice(1).toLowerCase()}</option>)}</select></label>}<label className="field"><span className="field__label">Sort</span><select value={filters.sort} onChange={(event) => updateUrl({ sort: event.target.value })}>{config.sorts.map((sort) => <option key={sort.value} value={sort.value}>{sort.label}</option>)}</select></label>{hasActiveFilters(filters) && <button className="text-button documents-clear" type="button" onClick={clearFilters}>Clear filters</button>}</div>
      {documentState.status === 'loading' && <div className="documents-feedback" role="status"><LoadingState label="Loading documents..." /></div>}
      {documentState.status === 'error' && <RetryState message="We couldn't load these documents. Your records are safe." onRetry={documentState.retry} />}
      {documentState.status === 'success' && documents.length === 0 && <EmptyState title={hasActiveFilters(filters) ? 'No matching documents' : `No ${config.label.toLowerCase()} yet`} description={hasActiveFilters(filters) ? 'Try changing or clearing the filters.' : `Create your first ${config.singular} to start building your document history.`} action={!hasActiveFilters(filters) ? <Link className="button" to={`/documents/${config.pathSegment}/new`}>Create {config.singular}</Link> : undefined} />}
      {documentState.status === 'success' && documents.length > 0 && <><div className="documents-table-wrap"><table className="documents-table"><caption className="sr-only">{config.label}</caption><thead><tr><th scope="col">Document</th><th scope="col">Client</th><th scope="col">Issue date</th><th scope="col">Amount</th><th scope="col">Status</th><th scope="col"><span className="sr-only">Actions</span></th></tr></thead><tbody>{documents.map((document) => { const display = formatDocumentRow(document, filters.type, clientMap.get(document.client_id)?.name); return <tr key={document.id}><th scope="row"><Link className="documents-document-link" to={documentDetailPath(document, filters.type)}><span>{display.typeLabel}</span><strong>{display.reference}</strong></Link></th><td data-label="Client" title={display.clientName}>{display.clientName}</td><td data-label="Issue date">{display.date}</td><td data-label="Amount" className="documents-table__amount">{display.amount}</td><td data-label="Status"><span className={`status-badge status-badge--${display.statusClass}`}>{display.status}</span></td><td data-label="Actions" className="documents-table__actions"><Link className="text-link" to={documentDetailPath(document, filters.type)}>Open</Link>{canEditDocument(document, filters.type) && <Link className="text-link" to={documentEditPath(document, filters.type)}>Edit</Link>}</td></tr>; })}</tbody></table></div><div className="documents-pagination"><span>Showing {((filters.page - 1) * meta.page_size) + 1}-{Math.min(filters.page * meta.page_size, meta.total)} of {meta.total}</span><div><button className="button button--secondary" type="button" disabled={filters.page <= 1} onClick={() => updateUrl({ page: filters.page - 1 }, false)}>Previous</button><button className="button button--secondary" type="button" disabled={filters.page >= totalPages} onClick={() => updateUrl({ page: filters.page + 1 }, false)}>Next</button></div></div></>}
      {clientsState.status === 'error' && <p className="documents-filter-note">Client names are temporarily unavailable; document search still works.</p>}
    </div>
  </section>;
}
