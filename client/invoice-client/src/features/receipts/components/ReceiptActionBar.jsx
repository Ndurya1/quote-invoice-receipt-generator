import { Link } from 'react-router-dom';
import { receiptEditPath, isReceiptEditable } from '../receiptData.js';

export default function ReceiptActionBar({ receipt, onDelete, pending = false }) {
  if (!isReceiptEditable(receipt)) return null;
  return <div className="document-action-bar" aria-label="Receipt actions"><div className="document-action-group document-action-group--management" aria-label="Document management actions"><Link className="button button--secondary" to={receiptEditPath(receipt.id)}>Edit</Link><button className="button button--danger-ghost" type="button" onClick={onDelete} disabled={pending}>Delete</button></div></div>;
}
