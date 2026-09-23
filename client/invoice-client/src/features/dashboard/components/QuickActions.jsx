import { Link } from 'react-router-dom';
import { routePaths } from '../../../utils/routePaths.js';

export default function QuickActions() {
  return (
    <div className="dashboard-quick-actions" aria-label="Quick document actions">
      <Link className="button" to={routePaths.quotationsNew}>New quotation</Link>
      <Link className="button button--secondary" to={routePaths.invoicesNew}>New invoice</Link>
      <Link className="dashboard-quick-actions__link" to={routePaths.documents}>View documents</Link>
    </div>
  );
}
