import { fieldErrorsFromDetails } from '../../api/apiErrors.js';

export const clientFormFields = ['name', 'email', 'phone', 'address'];
export const clientListDefaults = { page: 1, page_size: 20, search: '', sort: '-created_at' };
const supportedSorts = new Set(['name', '-name', 'created_at', '-created_at', 'id', '-id']);

export function clientFormValues(client = {}) {
  return clientFormFields.reduce((values, field) => ({ ...values, [field]: client[field] ?? '' }), {});
}

function trimmedOrNull(value) {
  const trimmed = typeof value === 'string' ? value.trim() : '';
  return trimmed || null;
}

export function validateClientValues(values = {}) {
  const errors = {};
  const name = typeof values.name === 'string' ? values.name.trim() : '';
  const email = trimmedOrNull(values.email);
  const phone = trimmedOrNull(values.phone);

  if (!name) errors.name = 'Enter a client name.';
  else if (name.length > 160) errors.name = 'Client name must be 160 characters or fewer.';
  if (email && (email.length > 255 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) errors.email = 'Enter a valid email address.';
  if (phone && phone.length > 30) errors.phone = 'Phone must be 30 characters or fewer.';
  return errors;
}

export function serializeClientCreate(values = {}) {
  return {
    name: values.name.trim(),
    email: trimmedOrNull(values.email),
    phone: trimmedOrNull(values.phone),
    address: trimmedOrNull(values.address),
  };
}

export function serializeClientPatch(values = {}, original = {}) {
  const next = serializeClientCreate(values);
  const previous = serializeClientCreate(clientFormValues(original));
  return clientFormFields.reduce((payload, field) => (
    next[field] !== previous[field] ? { ...payload, [field]: next[field] } : payload
  ), {});
}

export function readClientListQuery(searchParams) {
  const page = Math.max(1, Number.parseInt(searchParams.get('page') || clientListDefaults.page, 10) || clientListDefaults.page);
  const pageSize = Math.min(100, Math.max(1, Number.parseInt(searchParams.get('page_size') || clientListDefaults.page_size, 10) || clientListDefaults.page_size));
  const sort = supportedSorts.has(searchParams.get('sort')) ? searchParams.get('sort') : clientListDefaults.sort;
  return { page, page_size: pageSize, search: searchParams.get('search')?.trim() || '', sort };
}

export function clientListSearchParams(query) {
  const params = new URLSearchParams();
  if (query.page !== clientListDefaults.page) params.set('page', query.page);
  if (query.page_size !== clientListDefaults.page_size) params.set('page_size', query.page_size);
  if (query.search) params.set('search', query.search);
  if (query.sort !== clientListDefaults.sort) params.set('sort', query.sort);
  return params;
}

export function clientListParams(query) {
  return {
    page: query.page,
    page_size: query.page_size,
    ...(query.search ? { search: query.search } : {}),
    ...(query.sort ? { sort: query.sort } : {}),
  };
}

export function clientDetailPath(clientId) {
  return `/clients/${encodeURIComponent(clientId)}`;
}

export function clientEditPath(clientId) {
  return `${clientDetailPath(clientId)}/edit`;
}

export function clientDocumentsPath(type, clientId) {
  return `/documents?type=${encodeURIComponent(type)}&client_id=${encodeURIComponent(clientId)}`;
}

export function clientErrorMessage(error) {
  if (error?.code === 'CLIENT_IN_USE') return 'This client cannot be deleted because documents reference this record.';
  if (error?.code === 'CLIENT_NOT_FOUND') return 'This client could not be found or is no longer available.';
  return error?.message || 'Something went wrong. Please try again.';
}

export function clientFieldErrors(error) {
  return fieldErrorsFromDetails(error?.details);
}

export function clientListDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(date);
}
