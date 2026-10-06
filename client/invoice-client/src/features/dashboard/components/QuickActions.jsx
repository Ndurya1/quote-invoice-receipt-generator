import { FilePlus2, FileText, FolderOpen } from 'lucide-react';
import { Link } from 'react-router-dom';
import { routePaths } from '../../../utils/routePaths.js';

export default function QuickActions() {
  return (
    <div className="dashboard-quick-actions" aria-label="Quick document actions">
      <Link className="dashboard-quick-action dashboard-quick-action--primary" to={routePaths.quotationsNew}>
        <span className="dashboard-quick-action__icon"><FilePlus2 size={18} aria-hidden="true" /></span>
        <span><strong>New quotation</strong><small>Price the work and send it for approval.</small></span>
      </Link>
      <Link className="dashboard-quick-action" to={routePaths.invoicesNew}>
        <span className="dashboard-quick-action__icon"><FileText size={18} aria-hidden="true" /></span>
        <span><strong>New invoice</strong><small>Bill a client directly or from a quotation.</small></span>
      </Link>
      <Link className="dashboard-quick-action dashboard-quick-action--quiet" to={routePaths.documents}>
        <span className="dashboard-quick-action__icon"><FolderOpen size={18} aria-hidden="true" /></span>
        <span><strong>View documents</strong><small>Find quotations, invoices, and receipts.</small></span>
      </Link>
    </div>
  );
}
