import { formatCurrency } from '../../utils/currencyFormat.js';
import { formatDate } from '../../utils/dateFormat.js';
import { documentTypeLabel } from '../../utils/documentFormat.js';
import { statusLabel } from '../../utils/statusFormat.js';
import { allowedDocumentActions } from './documentActions.js';

const configs = {
  quotations: {
    label: 'Quotations', singular: 'quotation', numberField: 'quote_number', pathSegment: 'quotations',
    statuses: ['DRAFT', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CONVERTED'],
    sorts: [{ value: '-created_at', label: 'Newest first' }, { value: 'issue_date', label: 'Issue date' }, { value: 'expiry_date', label: 'Expiry date' }, { value: 'quote_number', label: 'Quotation number' }, { value: 'total', label: 'Amount' }],
  },
  invoices: {
    label: 'Invoices', singular: 'invoice', numberField: 'invoice_number', pathSegment: 'invoices',
    statuses: ['DRAFT', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED'],
    sorts: [{ value: '-created_at', label: 'Newest first' }, { value: 'issue_date', label: 'Issue date' }, { value: 'due_date', label: 'Due date' }, { value: 'invoice_number', label: 'Invoice number' }, { value: 'total', label: 'Amount' }],
  },
  receipts: {
    label: 'Receipts', singular: 'receipt', numberField: 'receipt_number', pathSegment: 'receipts',
    statuses: [],
    sorts: [{ value: '-created_at', label: 'Newest first' }, { value: 'issue_date', label: 'Issue date' }, { value: 'receipt_number', label: 'Receipt number' }, { value: 'total', label: 'Amount' }],
  },
};

export const documentListTypes = Object.keys(configs);

export function documentListConfig(type = 'quotations') {
  return configs[documentListTypes.includes(type) ? type : 'quotations'];
}

export function readDocumentFilters(searchParams) {
  const requestedType = searchParams.get('type');
  const type = documentListTypes.includes(requestedType) ? requestedType : 'quotations';
  const config = documentListConfig(type);
  const requestedStatus = searchParams.get('status') || '';
  const requestedSort = searchParams.get('sort') || '-created_at';
  return {
    type,
    page: Math.max(1, Number(searchParams.get('page')) || 1),
    page_size: Math.min(100, Math.max(1, Number(searchParams.get('page_size')) || 20)),
    search: searchParams.get('search') || '',
    client_id: searchParams.get('client_id') || '',
    status: config.statuses.includes(requestedStatus) ? requestedStatus : '',
    sort: config.sorts.some((option) => option.value === requestedSort) ? requestedSort : '-created_at',
  };
}

export function documentFiltersSearchParams(filters) {
  const config = documentListConfig(filters.type);
  const params = new URLSearchParams({ type: filters.type });
  if (filters.page > 1) params.set('page', String(filters.page));
  if (filters.page_size !== 20) params.set('page_size', String(filters.page_size));
  if (filters.search) params.set('search', filters.search);
  if (filters.client_id) params.set('client_id', filters.client_id);
  if (filters.status && config.statuses.includes(filters.status)) params.set('status', filters.status);
  if (filters.sort && config.sorts.some((option) => option.value === filters.sort) && filters.sort !== '-created_at') params.set('sort', filters.sort);
  return params;
}

export function documentListQuery(filters) {
  const config = documentListConfig(filters.type);
  const query = { page: filters.page, page_size: filters.page_size, search: filters.search || undefined, client_id: filters.client_id || undefined, sort: filters.sort || undefined };
  if (config.statuses.length && filters.status) query.status = filters.status;
  return query;
}

export function documentDetailPath(document, type) {
  const config = documentListConfig(type);
  return `/documents/${config.pathSegment}/${encodeURIComponent(document.id)}`;
}

export function documentEditPath(document, type) {
  return `${documentDetailPath(document, type)}/edit`;
}

export function canEditDocument(document, type) {
  const internalType = type === 'quotations' ? 'quotation' : type === 'invoices' ? 'invoice' : 'receipt';
  return allowedDocumentActions({ type: internalType, status: document.status, sourceQuoteId: document.source_quote_id, sourceInvoiceId: document.source_invoice_id }).includes('edit');
}

export function documentReference(document, type) {
  return document?.[documentListConfig(type).numberField] || 'No reference';
}

export function documentStatusText(document, type) {
  return type === 'receipts' ? 'Issued' : statusLabel(document?.status) || 'Unknown';
}

export function documentStatusClass(document, type) {
  return type === 'receipts' ? 'is-issued' : String(document?.status || 'unknown').toLowerCase();
}

export function formatDocumentRow(document, type, clientName = '') {
  return {
    typeLabel: documentTypeLabel(type === 'quotations' ? 'quote' : type === 'invoices' ? 'invoice' : 'receipt'),
    reference: documentReference(document, type),
    clientName: clientName || document.client_name || document.client_id || 'Unknown client',
    date: formatDate(document.issue_date),
    amount: formatCurrency(document.total, document.currency),
    status: documentStatusText(document, type),
    statusClass: documentStatusClass(document, type),
  };
}
