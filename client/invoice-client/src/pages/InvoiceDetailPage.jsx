import { useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { cancelInvoice, convertInvoice, deleteInvoice, markInvoicePaid, markInvoiceSent } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useAuth } from '../auth/useAuth.js';
import { useDataCache } from '../app/useDataCache.js';
import ConfirmDialog from '../components/overlays/ConfirmDialog.jsx';
import { useClient } from '../features/clients/useClients.js';
import DocumentCanvas from '../features/documents/components/DocumentCanvas.jsx';
import PdfDownloadButton from '../features/documents/components/PdfDownloadButton.jsx';
import { invoiceErrorMessage, invoiceListPath } from '../features/invoices/invoiceData.js';
import { convertPreviewInvoice, deletePreviewInvoice, transitionPreviewInvoice } from '../features/invoices/invoicePreview.js';
import InvoiceActionBar from '../features/invoices/components/InvoiceActionBar.jsx';
import InvoiceReceiptConversionDialog from '../features/invoices/components/InvoiceReceiptConversionDialog.jsx';
import { useInvoice } from '../features/invoices/useInvoices.js';

export default function InvoiceDetailPage() {
  const { invoiceId } = useParams();
  const invoiceState = useInvoice(invoiceId);
  if (invoiceState.status === 'loading') return <div className="document-feedback">Loading invoice…</div>;
  if (invoiceState.status === 'error') return <div className="document-feedback document-feedback--error"><strong>{invoiceErrorMessage(invoiceState.error)}</strong><button className="button button--secondary" type="button" onClick={invoiceState.retry}>Try again</button></div>;
  return <InvoiceDetailLoaded invoice={invoiceState.data} retry={invoiceState.retry} />;
}

function InvoiceDetailLoaded({ invoice, retry }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { businessProfile } = useAuth();
  const cache = useDataCache();
  const { data: client } = useClient(invoice.client_id);
  const [confirmAction, setConfirmAction] = useState('');
  const [pending, setPending] = useState('');
  const [error, setError] = useState('');
  const [conversionOpen, setConversionOpen] = useState(false);
  const [conversionPending, setConversionPending] = useState(false);
  const [conversionError, setConversionError] = useState('');

  function invalidate() {
    cache.remove(`invoices:detail:${invoice.id}`);
    cache.removeByPrefix('invoices:list:');
    cache.remove('dashboard:summary');
  }

  async function confirmActionHandler() {
    setPending(confirmAction);
    setError('');
    try {
      if (isAuthPreviewEnabled) {
        if (confirmAction === 'delete') deletePreviewInvoice(invoice.id);
        else transitionPreviewInvoice(invoice.id, confirmAction === 'markSent' ? 'SENT' : confirmAction === 'markPaid' ? 'PAID' : 'CANCELLED');
      } else if (confirmAction === 'delete') await deleteInvoice(invoice.id);
      else if (confirmAction === 'markSent') await markInvoiceSent(invoice.id);
      else if (confirmAction === 'markPaid') await markInvoicePaid(invoice.id);
      else if (confirmAction === 'cancel') await cancelInvoice(invoice.id);
      invalidate();
      if (confirmAction === 'delete') navigate(invoiceListPath, { replace: true, state: { message: `${invoice.invoice_number} was deleted.` } });
      else retry();
      setConfirmAction('');
    } catch (actionError) {
      if (actionError.status === 409) { invalidate(); retry(); }
      setError(invoiceErrorMessage(actionError));
    } finally {
      setPending('');
    }
  }

  async function convert(values) {
    setConversionPending(true);
    setConversionError('');
    try {
      const receipt = isAuthPreviewEnabled ? convertPreviewInvoice(invoice.id, values) : await convertInvoice(invoice.id, values);
      invalidate();
      navigate(`/documents/receipts/${encodeURIComponent(receipt.id)}`, { replace: true, state: { message: 'Receipt created from invoice.' } });
    } catch (conversionActionError) {
      if (conversionActionError.status === 409) { invalidate(); retry(); }
      setConversionError(invoiceErrorMessage(conversionActionError));
    } finally {
      setConversionPending(false);
    }
  }

  const confirmCopy = {
    delete: ['Delete invoice?', 'This permanently removes the draft invoice when it is eligible for deletion.'],
    markSent: ['Mark invoice as sent?', 'This records that you sent the downloaded invoice externally.'],
    markPaid: ['Mark invoice as paid?', 'This records business information only; no payment is processed by the platform.'],
    cancel: ['Cancel invoice?', 'Cancellation is terminal and prevents future receipt conversion.'],
  }[confirmAction];

  return <section className="document-page" aria-labelledby="invoice-detail-title">
    <header className="page-header document-detail-header"><div><h1 id="invoice-detail-title">{invoice.invoice_number}</h1><p className="page-header__description">Invoice for {client?.name || 'the selected client'}.</p></div><div className="page-header__actions"><PdfDownloadButton type="invoice" id={invoice.id} /></div></header>
    {location.state?.message && <div className="alert alert--success" role="status">{location.state.message}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <div className="quotation-detail-actions"><InvoiceActionBar invoice={invoice} onAction={(action) => { setError(''); setConfirmAction(action); }} onConvert={() => { setConversionError(''); setConversionOpen(true); }} pending={pending} /></div>
    <DocumentCanvas document={invoice} client={client} businessProfile={businessProfile} type="invoice" />
    <ConfirmDialog open={Boolean(confirmAction)} title={confirmCopy?.[0] || ''} description={confirmCopy?.[1] || ''} destructive={confirmAction === 'delete' || confirmAction === 'cancel'} confirmLabel={confirmAction === 'delete' ? 'Delete invoice' : confirmAction === 'cancel' ? 'Cancel invoice' : 'Confirm'} pending={Boolean(pending)} onCancel={() => { setConfirmAction(''); setError(''); }} onConfirm={confirmActionHandler}>{error ? <p className="form-error" role="alert">{error}</p> : undefined}</ConfirmDialog>
    <InvoiceReceiptConversionDialog open={conversionOpen} invoice={invoice} pending={conversionPending} error={conversionError} onCancel={() => setConversionOpen(false)} onConfirm={convert} />
  </section>;
}
