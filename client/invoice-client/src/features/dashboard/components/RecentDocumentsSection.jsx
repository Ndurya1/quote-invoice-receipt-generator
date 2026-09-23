import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { documentDetailPath, documentTypeFilterOptions, filterRecentDocuments, formatRecentDocument, isEmptyDashboard } from '../dashboardData.js';
import { routePaths } from '../../../utils/routePaths.js';

function EmptyRecentState({ firstDocument }) {
  return (
    <div className="dashboard-empty-state">
      <h3>{firstDocument ? 'Create your first quotation' : 'No recent documents'}</h3>
      <p>{firstDocument ? 'Your business details will be reused on future quotations, invoices and receipts.' : 'New documents will appear here after you create them.'}</p>
      {firstDocument && (
        <div className="dashboard-empty-state__actions">
          <Link className="button" to={routePaths.quotationsNew}>Create quotation</Link>
          <Link className="button button--secondary" to={routePaths.invoicesNew}>Create invoice</Link>
        </div>
      )}
    </div>
  );
}

export default function RecentDocumentsSection({ summary }) {
  const [filter, setFilter] = useState('all');
  const documents = useMemo(() => filterRecentDocuments(summary.recentDocuments, filter), [filter, summary.recentDocuments]);
  const firstDocument = isEmptyDashboard(summary);

  return (
    <section className="dashboard-recent" aria-labelledby="recent-documents-title">
      <div className="dashboard-section-heading">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2 id="recent-documents-title">Recent documents</h2>
        </div>
        <div className="dashboard-section-heading__controls">
          <label className="dashboard-filter">
            <span className="sr-only">Filter recent documents</span>
            <select value={filter} onChange={(event) => setFilter(event.target.value)}>
              {documentTypeFilterOptions().map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <Link className="text-link" to={routePaths.documents}>View all</Link>
        </div>
      </div>
      {documents.length === 0 ? (
        <EmptyRecentState firstDocument={firstDocument} />
      ) : (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <caption className="sr-only">The five most recently created documents</caption>
            <thead>
              <tr><th scope="col">Document</th><th scope="col">Client</th><th scope="col">Date</th><th scope="col">Amount</th><th scope="col">Status</th><th scope="col"><span className="sr-only">Action</span></th></tr>
            </thead>
            <tbody>
              {documents.map((document) => {
                const display = formatRecentDocument(document);
                return (
                  <tr key={`${document.type}-${document.id}`}>
                    <th scope="row"><Link className="dashboard-document-link" to={documentDetailPath(document)}><span>{display.typeLabel}</span><strong>{display.reference}</strong></Link></th>
                    <td data-label="Client" title={display.clientName}>{display.clientName}</td>
                    <td data-label="Date">{display.date}</td>
                    <td data-label="Amount" className="dashboard-table__amount">{display.amount}</td>
                    <td data-label="Status"><span className={`status-badge status-badge--${display.statusClass}`}>{display.status}</span></td>
                    <td data-label="Action"><Link className="text-link" to={documentDetailPath(document)}>Open</Link></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="dashboard-recent__scope">Showing up to five recent documents. Use View all for the complete workspace.</p>
    </section>
  );
}
