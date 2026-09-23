import { documentTypeLabel } from '../../utils/documentFormat.js';
import { formatCurrency } from '../../utils/currencyFormat.js';
import { formatDate } from '../../utils/dateFormat.js';
import { statusLabel } from '../../utils/statusFormat.js';

const documentTypes = new Set(['quote', 'invoice', 'receipt']);
const documentPathSegments = { quote: 'quotations', invoice: 'invoices', receipt: 'receipts' };

function countGroup(group) {
  return {
    total: Number.isFinite(Number(group?.total)) ? Number(group.total) : 0,
    draft: Number.isFinite(Number(group?.draft)) ? Number(group.draft) : 0,
    sent: Number.isFinite(Number(group?.sent)) ? Number(group.sent) : 0,
    accepted: Number.isFinite(Number(group?.accepted)) ? Number(group.accepted) : 0,
    paid: Number.isFinite(Number(group?.paid)) ? Number(group.paid) : 0,
    overdue: Number.isFinite(Number(group?.overdue)) ? Number(group.overdue) : 0,
  };
}

export function normalizeDashboardSummary(summary) {
  return {
    quotes: countGroup(summary?.quotes),
    invoices: countGroup(summary?.invoices),
    receipts: countGroup(summary?.receipts),
    recentDocuments: Array.isArray(summary?.recent_documents) ? summary.recent_documents.slice(0, 5) : [],
  };
}

export function filterRecentDocuments(documents, filter = 'all') {
  if (filter === 'all') return documents;
  const type = filter === 'quotations' ? 'quote' : filter === 'invoices' ? 'invoice' : 'receipt';
  return documents.filter((document) => document.type === type);
}

export function documentDetailPath(document) {
  const segment = documentPathSegments[document?.type];
  if (!segment || !document?.id) return '/documents';
  return `/documents/${segment}/${encodeURIComponent(document.id)}`;
}

export function documentListFilterPath(type, status) {
  const params = new URLSearchParams({ type });
  if (status) params.set('status', status);
  return `/documents?${params.toString()}`;
}

export function isEmptyDashboard(summary) {
  return summary.quotes.total === 0 && summary.invoices.total === 0 && summary.receipts.total === 0 && summary.recentDocuments.length === 0;
}

export function documentTypeFilterOptions() {
  return [
    { value: 'all', label: 'All' },
    { value: 'quotations', label: 'Quotations' },
    { value: 'invoices', label: 'Invoices' },
    { value: 'receipts', label: 'Receipts' },
  ];
}

export function formatRecentDocument(document) {
  const type = documentTypes.has(document?.type) ? document.type : 'document';
  const receipt = type === 'receipt';
  return {
    typeLabel: documentTypeLabel(type),
    reference: document?.document_number || 'No reference',
    clientName: document?.client_name || 'No client',
    date: formatDate(document?.issue_date),
    amount: formatCurrency(document?.total, document?.currency),
    status: receipt ? 'Issued' : statusLabel(document?.status) || 'Unknown',
    statusClass: receipt ? 'is-issued' : String(document?.status || 'unknown').toLowerCase(),
  };
}
