function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

export function listPreviewDocuments(documents, { page = 1, page_size: pageSize = 20, status = '', client_id: clientId = '', search = '', sort = '-created_at' } = {}, getClient, numberField) {
  const normalizedSearch = String(search).trim().toLowerCase();
  const filtered = documents.filter((document) => {
    const client = getClient(document.client_id);
    const matchesStatus = !status || document.status === status;
    const matchesClient = !clientId || document.client_id === clientId;
    const searchable = [document[numberField], client?.name, document.notes].map((value) => String(value || '').toLowerCase());
    const matchesSearch = !normalizedSearch || searchable.some((value) => value.includes(normalizedSearch));
    return matchesStatus && matchesClient && matchesSearch;
  });
  const descending = String(sort).startsWith('-');
  const field = descending ? String(sort).slice(1) : String(sort);
  const ordered = [...filtered].sort((left, right) => {
    const leftValue = String(left[field] ?? '');
    const rightValue = String(right[field] ?? '');
    const result = leftValue.localeCompare(rightValue, undefined, { numeric: true });
    return descending ? -result : result;
  });
  const safePage = Math.max(1, Number(page) || 1);
  const safePageSize = Math.max(1, Number(pageSize) || 20);
  const start = (safePage - 1) * safePageSize;
  return {
    data: ordered.slice(start, start + safePageSize).map((document) => ({ ...clone(document), client_name: getClient(document.client_id)?.name || 'Unknown client' })),
    meta: { page: safePage, page_size: safePageSize, total: ordered.length },
  };
}
