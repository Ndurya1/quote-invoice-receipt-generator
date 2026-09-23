let previewClients = [
  { id: 'client-001', user_id: 'developer-preview-user', name: 'Future Hope', email: 'accounts@futurehope.example', phone: '+254 700 100 001', address: 'Nairobi, Kenya', created_at: '2026-08-12T09:00:00Z', updated_at: '2026-08-12T09:00:00Z' },
  { id: 'client-002', user_id: 'developer-preview-user', name: 'Acme Studio', email: 'hello@acme.example', phone: '+254 700 100 002', address: 'Westlands, Nairobi', created_at: '2026-08-22T09:00:00Z', updated_at: '2026-08-22T09:00:00Z' },
  { id: 'client-003', user_id: 'developer-preview-user', name: 'Juma & Co.', email: null, phone: '+254 700 100 003', address: null, created_at: '2026-09-02T09:00:00Z', updated_at: '2026-09-02T09:00:00Z' },
];

function clone(client) {
  return client ? { ...client } : client;
}

function sortClients(clients, sort) {
  const descending = sort.startsWith('-');
  const field = descending ? sort.slice(1) : sort;
  return [...clients].sort((left, right) => {
    const a = String(left[field] || '').toLowerCase();
    const b = String(right[field] || '').toLowerCase();
    const result = a.localeCompare(b);
    return descending ? -result : result;
  });
}

export function listPreviewClients({ page = 1, page_size: pageSize = 20, search = '', sort = '-created_at' } = {}) {
  const normalizedSearch = search.toLowerCase();
  const filtered = previewClients.filter((client) => [client.name, client.email, client.phone].some((value) => String(value || '').toLowerCase().includes(normalizedSearch)));
  const ordered = sort === '-created_at' ? [...filtered].reverse() : sortClients(filtered, sort);
  const start = (page - 1) * pageSize;
  return { data: ordered.slice(start, start + pageSize).map(clone), meta: { page, page_size: pageSize, total: ordered.length } };
}

export function getPreviewClient(clientId) {
  const existing = previewClients.find((client) => client.id === clientId);
  if (existing) return clone(existing);
  return { id: clientId, user_id: 'developer-preview-user', name: 'Developer Preview Client', email: 'client@example.com', phone: '+254 700 000 000', address: 'Preview address', created_at: '2026-09-01T09:00:00Z', updated_at: '2026-09-01T09:00:00Z' };
}

export function createPreviewClient(payload) {
  const now = new Date().toISOString();
  const client = { ...payload, id: `preview-client-${Date.now()}`, user_id: 'developer-preview-user', created_at: now, updated_at: now };
  previewClients = [client, ...previewClients];
  return clone(client);
}

export function updatePreviewClient(clientId, payload) {
  const existing = getPreviewClient(clientId);
  const updated = { ...existing, ...payload, id: clientId, updated_at: new Date().toISOString() };
  previewClients = previewClients.some((client) => client.id === clientId) ? previewClients.map((client) => client.id === clientId ? updated : client) : [updated, ...previewClients];
  return clone(updated);
}

export function deletePreviewClient(clientId) {
  previewClients = previewClients.filter((client) => client.id !== clientId);
}
