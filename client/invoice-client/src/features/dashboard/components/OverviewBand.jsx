import { Link } from 'react-router-dom';
import { documentListFilterPath } from '../dashboardData.js';

const metrics = [
  {
    key: 'outstandingInvoices',
    label: 'Outstanding invoices',
    supporting: 'sent or overdue',
    type: 'invoices',
    featured: true,
    value: (summary) => summary.invoices.sent + summary.invoices.overdue,
  },
  {
    key: 'paidInvoices',
    label: 'Paid invoices',
    supporting: 'recorded as paid',
    type: 'invoices',
    status: 'PAID',
    value: (summary) => summary.invoices.paid,
  },
  {
    key: 'quotes',
    label: 'Quotations',
    supporting: 'across your workspace',
    type: 'quotations',
    value: (summary) => summary.quotes.total,
  },
  {
    key: 'receipts',
    label: 'Receipts',
    supporting: 'issued to clients',
    type: 'receipts',
    value: (summary) => summary.receipts.total,
  },
];

export default function OverviewBand({ summary }) {
  return (
    <section className="dashboard-overview" aria-labelledby="dashboard-overview-title">
      <h2 id="dashboard-overview-title" className="sr-only">Document overview</h2>
      {metrics.map(({ key, label, supporting, type, status, featured, value }) => (
        <Link key={key} className={`dashboard-metric${featured ? ' dashboard-metric--featured' : ''}`} to={documentListFilterPath(type, status)}>
          <span className="dashboard-metric__label">{label}</span>
          <strong>{value(summary)}</strong>
          <span className="dashboard-metric__action">{supporting}</span>
        </Link>
      ))}
    </section>
  );
}
