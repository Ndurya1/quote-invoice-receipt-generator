const documentLabels = { quote: 'Quotation', invoice: 'Invoice', receipt: 'Receipt' };

export function documentTypeLabel(type) {
  return documentLabels[type] || 'Document';
}

export function documentListPath(type = 'quotations') {
  return `/documents?type=${encodeURIComponent(type)}`;
}
