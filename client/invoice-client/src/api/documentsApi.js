import { apiClient } from './apiClient.js';
import { collectionData, resourceData } from './apiResponse.js';

async function list(path, params, client) {
  return collectionData(await client.request(path, { query: params }));
}

async function get(path, client) {
  return resourceData(await client.request(path));
}

async function mutate(path, method, payload, client) {
  return resourceData(await client.request(path, { method, body: payload }));
}

export function listQuotations(params, client = apiClient) { return list('/quotes', params, client); }
export function getQuotation(id, client = apiClient) { return get(`/quotes/${id}`, client); }
export function createQuotation(payload, client = apiClient) { return mutate('/quotes', 'POST', payload, client); }
export function updateQuotation(id, payload, client = apiClient) { return mutate(`/quotes/${id}`, 'PATCH', payload, client); }
export async function deleteQuotation(id, client = apiClient) { await client.request(`/quotes/${id}`, { method: 'DELETE' }); }
export function markQuotationSent(id, client = apiClient) { return mutate(`/quotes/${id}/send`, 'POST', undefined, client); }
export function acceptQuotation(id, client = apiClient) { return mutate(`/quotes/${id}/accept`, 'POST', undefined, client); }
export function rejectQuotation(id, client = apiClient) { return mutate(`/quotes/${id}/reject`, 'POST', undefined, client); }
export function convertQuotation(id, payload, client = apiClient) { return mutate(`/quotes/${id}/convert`, 'POST', payload, client); }

export function listInvoices(params, client = apiClient) { return list('/invoices', params, client); }
export function getInvoice(id, client = apiClient) { return get(`/invoices/${id}`, client); }
export function createInvoice(payload, client = apiClient) { return mutate('/invoices', 'POST', payload, client); }
export function updateInvoice(id, payload, client = apiClient) { return mutate(`/invoices/${id}`, 'PATCH', payload, client); }
export async function deleteInvoice(id, client = apiClient) { await client.request(`/invoices/${id}`, { method: 'DELETE' }); }
export function markInvoiceSent(id, client = apiClient) { return mutate(`/invoices/${id}/send`, 'POST', undefined, client); }
export function markInvoicePaid(id, client = apiClient) { return mutate(`/invoices/${id}/mark-paid`, 'POST', undefined, client); }
export function cancelInvoice(id, client = apiClient) { return mutate(`/invoices/${id}/cancel`, 'POST', undefined, client); }
export function convertInvoice(id, payload, client = apiClient) { return mutate(`/invoices/${id}/convert`, 'POST', payload, client); }

export function listReceipts(params, client = apiClient) { return list('/receipts', params, client); }
export function getReceipt(id, client = apiClient) { return get(`/receipts/${id}`, client); }
export function createReceipt(payload, client = apiClient) { return mutate('/receipts', 'POST', payload, client); }
export function updateReceipt(id, payload, client = apiClient) { return mutate(`/receipts/${id}`, 'PATCH', payload, client); }
export async function deleteReceipt(id, client = apiClient) { await client.request(`/receipts/${id}`, { method: 'DELETE' }); }
