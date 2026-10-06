import { AlertTriangle, Clock3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { documentListFilterPath } from '../dashboardData.js';

function pluralize(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export default function DashboardAttention({ summary }) {
  const items = [];
  if (summary.invoices.overdue > 0) {
    items.push({
      key: 'overdue',
      icon: AlertTriangle,
      tone: 'warning',
      title: `${pluralize(summary.invoices.overdue, 'invoice')} overdue`,
      detail: 'Follow up before it slips further.',
      action: 'Review invoices',
      to: documentListFilterPath('invoices', 'OVERDUE'),
    });
  }
  if (summary.quotes.sent > 0) {
    items.push({
      key: 'quotes',
      icon: Clock3,
      tone: 'neutral',
      title: `${pluralize(summary.quotes.sent, 'quotation')} awaiting response`,
      detail: 'Check in when the timing is right.',
      action: 'View quotations',
      to: documentListFilterPath('quotations', 'SENT'),
    });
  }

  if (items.length === 0) return null;

  return (
    <aside className="dashboard-attention" aria-labelledby="dashboard-attention-title">
      <div className="dashboard-panel-heading">
        <div>
          <p className="eyebrow">Follow-up</p>
          <h2 id="dashboard-attention-title">Needs attention</h2>
        </div>
        <span className="dashboard-panel-heading__count">{items.length} {items.length === 1 ? 'item' : 'items'}</span>
      </div>
      <div className="dashboard-attention__items">
        {items.map(({ key, icon: Icon, tone, title, detail, action, to }) => (
          <div className="dashboard-attention__item" key={key}>
            <div className={`dashboard-attention__marker dashboard-attention__marker--${tone}`}>
              <Icon size={16} aria-hidden="true" />
            </div>
            <div className="dashboard-attention__copy">
              <strong>{title}</strong>
              <span>{detail}</span>
              <Link className="text-link" to={to}>{action}</Link>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
