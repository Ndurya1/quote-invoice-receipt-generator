import { apiClient } from './apiClient.js';
import { collectionData, resourceData } from './apiResponse.js';

export async function listClients(params, client = apiClient, options = {}) {
  return collectionData(await client.request('/clients', { ...options, query: params }));
}

export async function getClient(clientId, client = apiClient, options = {}) {
  return resourceData(await client.request(`/clients/${clientId}`, options));
}

export async function createClient(payload, client = apiClient, options = {}) {
  return resourceData(await client.request('/clients', { ...options, method: 'POST', body: payload }));
}

export async function updateClient(clientId, payload, client = apiClient, options = {}) {
  return resourceData(await client.request(`/clients/${clientId}`, { ...options, method: 'PATCH', body: payload }));
}

export async function deleteClient(clientId, client = apiClient, options = {}) {
  await client.request(`/clients/${clientId}`, { ...options, method: 'DELETE' });
}
