import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import { acceptQuotation, deleteQuotation, markQuotationSent, rejectQuotation, convertQuotation } from '../api/documentsApi.js';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import { useAuth } from '../auth/useAuth.js';
import { useDataCache } from '../app/useDataCache.js';
import ConfirmDialog from '../components/overlays/ConfirmDialog.jsx';
import { useClient } from '../features/clients/useClients.js';
import PdfDownloadButton from '../features/documents/components/PdfDownloadButton.jsx';
import { transitionPreviewQuotation, deletePreviewQuotation, convertPreviewQuotation } from '../features/quotations/quotationPreview.js';
import { quotationErrorMessage, quotationListPath } from '../features/quotations/quotationData.js';
import QuotationActionBar from '../features/quotations/components/QuotationActionBar.jsx';
import QuotationConversionDialog from '../features/quotations/components/QuotationConversionDialog.jsx';
import QuotationCanvas from '../features/quotations/components/QuotationCanvas.jsx';
import { useQuotation } from '../features/quotations/useQuotations.js';

export default function QuotationDetailPage() {
  const { quoteId } = useParams();
  const quotationState = useQuotation(quoteId);
  if (quotationState.status === 'loading') return <div className="document-feedback">Loading quotation…</div>;
  if (quotationState.status === 'error') return <div className="document-feedback document-feedback--error"><strong>{quotationErrorMessage(quotationState.error)}</strong><button className="button button--secondary" type="button" onClick={quotationState.retry}>Try again</button></div>;
  return <QuotationDetailLoaded quotation={quotationState.data} retry={quotationState.retry} />;
}

function QuotationDetailLoaded({ quotation, retry }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { businessProfile } = useAuth();
  const cache = useDataCache();
  const { data: client } = useClient(quotation.client_id);
  const [confirmAction, setConfirmAction] = useState('');
  const [pending, setPending] = useState('');
  const [error, setError] = useState('');
  const [conversionOpen, setConversionOpen] = useState(false);
  const [conversionPending, setConversionPending] = useState(false);
  const [conversionError, setConversionError] = useState('');

  function invalidate() {
    cache.remove(`quotations:detail:${quotation.id}`);
    cache.removeByPrefix('quotations:list:');
    cache.remove('dashboard:summary');
  }

  async function confirmActionHandler() {
    setPending(confirmAction);
    setError('');
    try {
      if (isAuthPreviewEnabled) {
        if (confirmAction === 'delete') deletePreviewQuotation(quotation.id);
        else transitionPreviewQuotation(quotation.id, confirmAction === 'markSent' ? 'SENT' : confirmAction === 'accept' ? 'ACCEPTED' : 'REJECTED');
      } else if (confirmAction === 'delete') await deleteQuotation(quotation.id);
      else if (confirmAction === 'markSent') await markQuotationSent(quotation.id);
      else if (confirmAction === 'accept') await acceptQuotation(quotation.id);
      else if (confirmAction === 'reject') await rejectQuotation(quotation.id);
      invalidate();
      if (confirmAction === 'delete') navigate(quotationListPath, { replace: true, state: { message: `${quotation.quote_number} was deleted.` } });
      else retry();
      setConfirmAction('');
    } catch (actionError) {
      if (actionError.status === 409) { invalidate(); retry(); }
      setError(quotationErrorMessage(actionError));
    } finally {
      setPending('');
    }
  }

  async function convert(values) {
    setConversionPending(true);
    setConversionError('');
    try {
      const invoice = isAuthPreviewEnabled ? convertPreviewQuotation(quotation.id, values) : await convertQuotation(quotation.id, values);
      invalidate();
      navigate(`/documents/invoices/${encodeURIComponent(invoice.id)}`, { replace: true, state: { message: 'Invoice created from quotation.' } });
    } catch (conversionActionError) {
      if (conversionActionError.status === 409) { invalidate(); retry(); }
      setConversionError(quotationErrorMessage(conversionActionError));
    } finally {
      setConversionPending(false);
    }
  }

  const confirmCopy = {
    delete: ['Delete quotation?', 'This permanently removes the draft quotation.'],
    markSent: ['Mark quotation as sent?', 'This records that you sent the downloaded quotation externally.'],
    accept: ['Accept quotation?', 'This makes the quotation eligible for invoice conversion.'],
    reject: ['Reject quotation?', 'Rejected quotations cannot be sent, edited, or converted.'],
  }[confirmAction];

  return <section className="document-page" aria-labelledby="quotation-detail-title">
    <header className="page-header document-detail-header"><div><h1 id="quotation-detail-title">{quotation.quote_number}</h1><p className="page-header__description">Quotation for {client?.name || 'the selected client'}.</p></div><div className="page-header__actions"><PdfDownloadButton type="quotation" id={quotation.id} /></div></header>
    {location.state?.message && <div className="alert alert--success" role="status">{location.state.message}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <div className="quotation-detail-actions"><QuotationActionBar quotation={quotation} onAction={(action) => { setError(''); setConfirmAction(action); }} onConvert={() => { setConversionError(''); setConversionOpen(true); }} pending={pending} /></div>
    <QuotationCanvas quotation={quotation} client={client} businessProfile={businessProfile} />
    {quotation.related_invoice_id && <section className="document-related-link"><h2>Related invoice</h2><Link className="text-link" to={`/documents/invoices/${encodeURIComponent(quotation.related_invoice_id)}`}>Open related invoice</Link></section>}
    <ConfirmDialog open={Boolean(confirmAction)} title={confirmCopy?.[0] || ''} description={confirmCopy?.[1] || ''} destructive={confirmAction === 'delete' || confirmAction === 'reject'} confirmLabel={confirmAction === 'delete' ? 'Delete quotation' : confirmAction === 'reject' ? 'Reject quotation' : 'Confirm'} pending={Boolean(pending)} onCancel={() => { setConfirmAction(''); setError(''); }} onConfirm={confirmActionHandler}>{error ? <p className="form-error" role="alert">{error}</p> : undefined}</ConfirmDialog>
    <QuotationConversionDialog open={conversionOpen} quotation={quotation} pending={conversionPending} error={conversionError} onCancel={() => setConversionOpen(false)} onConfirm={convert} />
  </section>;
}
