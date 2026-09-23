import { useState } from 'react';
import { downloadInvoicePdf, downloadQuotationPdf, downloadReceiptPdf } from '../../../api/pdfApi.js';
import { isAuthPreviewEnabled } from '../../../auth/authPreview.js';

const pdfDownloads = { quotation: downloadQuotationPdf, invoice: downloadInvoicePdf, receipt: downloadReceiptPdf };

export default function PdfDownloadButton({ type, id }) {
  const [state, setState] = useState('idle');
  async function download() {
    if (isAuthPreviewEnabled) { setState('preview'); return; }
    setState('loading');
    try {
      const { blob, filename } = await pdfDownloads[type](id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setState('idle');
    } catch { setState('error'); }
  }
  const label = state === 'loading' ? 'Preparing PDF…' : state === 'error' ? 'Retry PDF download' : 'Download PDF';
  return <div className="pdf-download-control"><button className="button button--secondary" type="button" onClick={download} disabled={state === 'loading'}>{label}</button>{state === 'preview' && <span className="field__helper" role="status">PDF download is available after this preview is saved.</span>}{state === 'error' && <span className="form-error" role="alert">We could not prepare the PDF. Try again.</span>}</div>;
}
