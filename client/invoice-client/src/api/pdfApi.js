import { apiClient } from './apiClient.js';

export function downloadQuotationPdf(id, client = apiClient) {
  return client.requestBlob(`/quotes/${id}/pdf`, { fallbackFilename: `quotation-${id}.pdf` });
}

export function downloadInvoicePdf(id, client = apiClient) {
  return client.requestBlob(`/invoices/${id}/pdf`, { fallbackFilename: `invoice-${id}.pdf` });
}

export function downloadReceiptPdf(id, client = apiClient) {
  return client.requestBlob(`/receipts/${id}/pdf`, { fallbackFilename: `receipt-${id}.pdf` });
}
