export function normalizeBaseUrl(value) {
  const rawValue = typeof value === 'string' && value.trim() ? value.trim() : '/api/v1';
  if (rawValue === '/') return '';
  return rawValue.replace(/\/+$/, '');
}

export function getApiBaseUrl(environment = import.meta.env) {
  return normalizeBaseUrl(environment?.VITE_API_BASE_URL);
}
