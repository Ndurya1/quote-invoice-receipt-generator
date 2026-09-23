import { useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { deleteReceipt } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useAuth } from '../auth/useAuth.js';
import { useDataCache } from '../app/useDataCache.js';
import ConfirmDialog from '../components/overlays/ConfirmDialog.jsx';
import { useClient } from '../features/clients/useClients.js';
import DocumentCanvas from '../features/documents/components/DocumentCanvas.jsx';
import PdfDownloadButton from '../features/documents/components/PdfDownloadButton.jsx';
import { deletePreviewReceipt } from '../features/receipts/receiptPreview.js';
import { isReceiptEditable, receiptErrorMessage, receiptListPath } from '../features/receipts/receiptData.js';
import ReceiptActionBar from '../features/receipts/components/ReceiptActionBar.jsx';
import { useReceipt } from '../features/receipts/useReceipts.js';

export default function ReceiptDetailPage() {
  const { receiptId } = useParams();
  const receiptState = useReceipt(receiptId);
  if (receiptState.status === 'loading') return <div className="document-feedback">Loading receipt...</div>;
  if (receiptState.status === 'error') return <div className="document-feedback document-feedback--error"><strong>{receiptErrorMessage(receiptState.error)}</strong><button className="button button--secondary" type="button" onClick={receiptState.retry}>Try again</button></div>;
  return <ReceiptDetailLoaded receipt={receiptState.data} retry={receiptState.retry} />;
}

function ReceiptDetailLoaded({ receipt, retry }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { businessProfile } = useAuth();
  const cache = useDataCache();
  const { data: client } = useClient(receipt.client_id);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');

  function invalidate() {
    cache.remove(`receipts:detail:${receipt.id}`);
    cache.removeByPrefix('receipts:list:');
    cache.removeByPrefix('documents:receipts:list:');
    cache.remove('dashboard:summary');
  }

  async function confirmDelete() {
    setPending(true);
    setError('');
    try {
      if (isAuthPreviewEnabled) deletePreviewReceipt(receipt.id);
      else await deleteReceipt(receipt.id);
      invalidate();
      navigate(receiptListPath, { replace: true, state: { message: `${receipt.receipt_number} was deleted.` } });
    } catch (deleteError) {
      if (deleteError.status === 409) { invalidate(); retry(); }
      setError(receiptErrorMessage(deleteError));
    } finally {
      setPending(false);
      setDeleteOpen(false);
    }
  }

  return <section className="document-page" aria-labelledby="receipt-detail-title"><header className="page-header document-detail-header"><div><h1 id="receipt-detail-title">{receipt.receipt_number}</h1><p className="page-header__description">Receipt for {client?.name || 'the selected client'}.</p></div><div className="page-header__actions"><PdfDownloadButton type="receipt" id={receipt.id} /></div></header>{location.state?.message && <div className="alert alert--success" role="status">{location.state.message}</div>}{error && <div className="form-error" role="alert">{error}</div>}{isReceiptEditable(receipt) && <div className="quotation-detail-actions"><ReceiptActionBar receipt={receipt} onDelete={() => { setError(''); setDeleteOpen(true); }} pending={pending} /></div>}<DocumentCanvas document={receipt} client={client} businessProfile={businessProfile} type="receipt" /><ConfirmDialog open={deleteOpen} title="Delete receipt?" description="This permanently removes the direct receipt. Invoice-linked receipts cannot be deleted." destructive confirmLabel="Delete receipt" pending={pending} onCancel={() => { setDeleteOpen(false); setError(''); }} onConfirm={confirmDelete}>{error ? <p className="form-error" role="alert">{error}</p> : undefined}</ConfirmDialog></section>;
}
