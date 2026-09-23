import assert from 'node:assert/strict';
import test from 'node:test';
import { downloadQuotationPdf } from '../src/api/pdfApi.js';
import { allowedDocumentActions } from '../src/features/documents/documentActions.js';
import { createPreviewClient, deletePreviewClient } from '../src/features/clients/clientPreview.js';
import { convertPreviewQuotation, createPreviewQuotation, deletePreviewQuotation, getPreviewQuotation, transitionPreviewQuotation } from '../src/features/quotations/quotationPreview.js';
import { createPreviewInvoice, deletePreviewInvoice, getPreviewInvoice, updatePreviewInvoice } from '../src/features/invoices/invoicePreview.js';
import { createPreviewReceipt, createPreviewReceiptFromInvoice, deletePreviewReceipt, getPreviewReceipt, updatePreviewReceipt } from '../src/features/receipts/receiptPreview.js';

function documentPayload(clientId, description = 'Integration service') {
  return { client_id: clientId, issue_date: '2026-09-23', currency: 'KES', tax_rate: '16.000', discount_type: 'NONE', discount_value: '0.00', items: [{ description, quantity: '1', unit_price: '1000.00', position: 0 }] };
}

test('covers the mocked new-user journey through quotation PDF download', async () => {
  const client = createPreviewClient({ name: 'Journey Client', email: 'journey@example.com', phone: null, address: null });
  const quotation = createPreviewQuotation(documentPayload(client.id, 'New-user service'));
  const pdfCalls = [];
  const pdf = await downloadQuotationPdf(quotation.id, {
    requestBlob: async (path, options) => {
      pdfCalls.push({ path, options });
      return { blob: new Blob(['pdf'], { type: 'application/pdf' }), filename: `quotation-${quotation.id}.pdf` };
    },
  });

  try {
    assert.equal(getPreviewQuotation(quotation.id).client_id, client.id);
    assert.equal(pdf.filename, `quotation-${quotation.id}.pdf`);
    assert.deepEqual(pdfCalls, [{ path: `/quotes/${quotation.id}/pdf`, options: { fallbackFilename: `quotation-${quotation.id}.pdf` } }]);
  } finally {
    deletePreviewQuotation(quotation.id);
    deletePreviewClient(client.id);
  }
});

test('covers quotation to invoice to paid receipt relationships', () => {
  const quotation = createPreviewQuotation(documentPayload('client-001', 'Connected service'));
  const accepted = transitionPreviewQuotation(quotation.id, 'ACCEPTED');
  const invoice = convertPreviewQuotation(quotation.id, { issue_date: '2026-09-23', due_date: '2026-10-23' });
  const paidInvoice = { ...invoice, status: 'PAID' };
  const receipt = createPreviewReceiptFromInvoice(paidInvoice, { issue_date: '2026-09-23' });

  try {
    assert.equal(accepted.status, 'ACCEPTED');
    assert.equal(getPreviewQuotation(quotation.id).status, 'CONVERTED');
    assert.equal(invoice.source_quote_id, quotation.id);
    assert.equal(receipt.source_invoice_id, invoice.id);
    assert.deepEqual(allowedDocumentActions({ type: 'quotation', status: 'CONVERTED' }), []);
    assert.deepEqual(allowedDocumentActions({ type: 'invoice', status: 'PAID' }), ['convertReceipt']);
    assert.deepEqual(allowedDocumentActions({ type: 'receipt', sourceInvoiceId: invoice.id }), []);
  } finally {
    deletePreviewQuotation(quotation.id);
  }
});

test('covers direct invoice and receipt editing with linked-record protection', async () => {
  const invoice = createPreviewInvoice(documentPayload('client-001', 'Direct invoice'));
  const directReceipt = createPreviewReceipt(documentPayload('client-001', 'Direct receipt'));
  await new Promise((resolve) => setTimeout(resolve, 2));
  const linkedReceipt = createPreviewReceiptFromInvoice(invoice, { issue_date: '2026-09-23' });

  try {
    assert.equal(updatePreviewInvoice(invoice.id, { ...invoice, notes: 'Updated invoice' }).notes, 'Updated invoice');
    assert.equal(updatePreviewReceipt(directReceipt.id, { ...directReceipt, notes: 'Updated receipt' }).notes, 'Updated receipt');
    assert.equal(getPreviewInvoice(invoice.id).notes, 'Updated invoice');
    assert.equal(getPreviewReceipt(directReceipt.id).notes, 'Updated receipt');
    assert.throws(() => updatePreviewReceipt(linkedReceipt.id, { notes: 'Cannot edit linked receipt' }), (error) => error.code === 'INVALID_RECEIPT_STATUS');
  } finally {
    deletePreviewInvoice(invoice.id);
    deletePreviewReceipt(directReceipt.id);
  }
});
