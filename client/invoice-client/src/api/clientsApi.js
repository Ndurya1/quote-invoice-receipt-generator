import { apiClient } from './apiClient.js';
import { collectionData, resourceData } from './apiResponse.js';

export async function listClients(params, client = apiClient) {
  return collectionData(await client.request('/clients', { query: params }));
}

export async function getClient(clientId, client = apiClient) {
  return resourceData(await client.request(`/clients/${clientId}`));
}

export async function createClient(payload, client = apiClient) {
  return resourceData(await client.request('/clients', { method: 'POST', body: payload }));
}

export async function updateClient(clientId, payload, client = apiClient) {
  return resourceData(await client.request(`/clients/${clientId}`, { method: 'PATCH', body: payload }));
}

export async function deleteClient(clientId, client = apiClient) {
  await client.request(`/clients/${clientId}`, { method: 'DELETE' });
}
