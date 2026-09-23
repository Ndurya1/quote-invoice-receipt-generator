import { FileCheck2, FileText, ReceiptText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { documentListFilterPath } from '../dashboardData.js';

const metrics = [
  { key: 'invoices', label: 'Invoices', type: 'invoices', icon: FileText, featured: true },
  { key: 'quotes', label: 'Quotations', type: 'quotations', icon: FileCheck2 },
  { key: 'paidInvoices', label: 'Paid invoices', type: 'invoices', status: 'PAID', icon: FileCheck2 },
  { key: 'receipts', label: 'Receipts', type: 'receipts', icon: ReceiptText },
];

export default function OverviewBand({ summary }) {
  return (
    <section className="dashboard-overview" aria-labelledby="dashboard-overview-title">
      <h2 id="dashboard-overview-title" className="sr-only">Document overview</h2>
      {metrics.map(({ key, label, type, status, icon: Icon, featured }) => (
        <Link key={key} className={`dashboard-metric${featured ? ' dashboard-metric--featured' : ''}`} to={documentListFilterPath(type, status)}>
          <span className="dashboard-metric__label"><Icon size={16} aria-hidden="true" />{label}</span>
          <strong>{key === 'paidInvoices' ? summary.invoices.paid : summary[key].total}</strong>
          <span className="dashboard-metric__action">View {label.toLowerCase()}</span>
        </Link>
      ))}
    </section>
  );
}
