import { apiClient } from './apiClient.js';
import { resourceData } from './apiResponse.js';

export async function getBusinessProfile(client = apiClient) {
  return resourceData(await client.request('/business-profile'));
}

export async function replaceBusinessProfile(payload, client = apiClient) {
  return resourceData(await client.request('/business-profile', { method: 'PUT', body: payload }));
}
