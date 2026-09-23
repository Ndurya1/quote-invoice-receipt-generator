import assert from 'node:assert/strict';
import test from 'node:test';
import {
  documentDetailPath,
  documentListFilterPath,
  filterRecentDocuments,
  formatRecentDocument,
  isEmptyDashboard,
  normalizeDashboardSummary,
} from '../src/features/dashboard/dashboardData.js';

test('normalizes dashboard counts and caps recent documents at five', () => {
  const summary = normalizeDashboardSummary({
    quotes: { total: 2 },
    invoices: { total: 4, paid: 1, overdue: 2 },
    receipts: { total: 3 },
    recent_documents: Array.from({ length: 6 }, (_, index) => ({ id: String(index), type: 'invoice' })),
  });

  assert.deepEqual(summary.quotes.total, 2);
  assert.deepEqual(summary.invoices.paid, 1);
  assert.deepEqual(summary.invoices.overdue, 2);
  assert.equal(summary.recentDocuments.length, 5);
});

test('uses safe zero defaults for incomplete dashboard responses', () => {
  const summary = normalizeDashboardSummary({});
  assert.deepEqual(summary, {
    quotes: { total: 0, draft: 0, sent: 0, accepted: 0, paid: 0, overdue: 0 },
    invoices: { total: 0, draft: 0, sent: 0, accepted: 0, paid: 0, overdue: 0 },
    receipts: { total: 0, draft: 0, sent: 0, accepted: 0, paid: 0, overdue: 0 },
    recentDocuments: [],
  });
  assert.equal(isEmptyDashboard(summary), true);
});

test('filters only the returned recent documents by type', () => {
  const documents = [
    { id: 'q1', type: 'quote' },
    { id: 'i1', type: 'invoice' },
    { id: 'r1', type: 'receipt' },
  ];
  assert.equal(filterRecentDocuments(documents, 'all').length, 3);
  assert.deepEqual(filterRecentDocuments(documents, 'quotations').map(({ id }) => id), ['q1']);
  assert.deepEqual(filterRecentDocuments(documents, 'invoices').map(({ id }) => id), ['i1']);
  assert.deepEqual(filterRecentDocuments(documents, 'receipts').map(({ id }) => id), ['r1']);
});

test('builds safe document links and supported list filters', () => {
  assert.equal(documentDetailPath({ type: 'quote', id: 'quote/1' }), '/documents/quotations/quote%2F1');
  assert.equal(documentDetailPath({ type: 'receipt', id: 'receipt-1' }), '/documents/receipts/receipt-1');
  assert.equal(documentDetailPath({ type: 'unknown', id: '1' }), '/documents');
  assert.equal(documentListFilterPath('invoices', 'OVERDUE'), '/documents?type=invoices&status=OVERDUE');
});

test('does not invent a receipt lifecycle status', () => {
  const display = formatRecentDocument({ type: 'receipt', total: '100', currency: 'KES', status: null });
  assert.equal(display.typeLabel, 'Receipt');
  assert.equal(display.status, 'Issued');
  assert.equal(display.statusClass, 'is-issued');
});
