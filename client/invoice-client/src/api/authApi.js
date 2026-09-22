import { apiClient } from './apiClient.js';
import { resourceData } from './apiResponse.js';

export async function register(payload, client = apiClient) {
  return resourceData(await client.request('/auth/register', { method: 'POST', body: payload }));
}

export async function login(payload, client = apiClient) {
  const response = await client.request('/auth/login', { method: 'POST', body: payload });
  client.sessionStore.saveTokens(response.data);
  return response.data;
}

export async function refresh(refreshToken, client = apiClient) {
  const response = await client.request('/auth/refresh', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    skipRefresh: true,
  });
  client.sessionStore.setAccessToken(response.data.access_token);
  return response.data;
}

export async function getCurrentUser(client = apiClient) {
  return resourceData(await client.request('/auth/me'));
}

export function logout(client = apiClient) {
  client.sessionStore.clear();
}
