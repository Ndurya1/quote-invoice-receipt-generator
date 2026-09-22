import { apiClient } from './apiClient.js';
import { resourceData } from './apiResponse.js';

export async function getDashboardSummary(client = apiClient) {
  return resourceData(await client.request('/dashboard/summary'));
}
