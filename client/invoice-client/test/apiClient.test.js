import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, SessionExpiredError } from '../src/api/apiErrors.js';
import { createApiClient } from '../src/api/apiClient.js';
import { createSessionStore } from '../src/api/sessionStore.js';

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } });
}

function memoryStorage() {
  const values = new Map();
  return { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) };
}

test('adds bearer auth and serializes query parameters', async () => {
  const store = createSessionStore(memoryStorage());
  store.saveTokens({ accessToken: 'access' });
  let request;
  const client = createApiClient({
    baseUrl: '/api/v1',
    session: store,
    fetchImpl: async (url, init) => {
      request = { url, init };
      return jsonResponse({ data: { ok: true } });
    },
  });
  const response = await client.request('/clients', { query: { page: 1, search: 'Acme Ltd' } });
  assert.deepEqual(response.data, { ok: true });
  assert.equal(request.url, '/api/v1/clients?page=1&search=Acme+Ltd');
  assert.equal(request.init.headers.get('Authorization'), 'Bearer access');
});

test('refreshes once and retries a failed authenticated request', async () => {
  const store = createSessionStore(memoryStorage());
  store.saveTokens({ accessToken: 'old-access', refreshToken: 'refresh' });
  const calls = [];
  const client = createApiClient({
    baseUrl: '/api/v1',
    session: store,
    fetchImpl: async (url) => {
      calls.push(url);
      if (url.endsWith('/protected')) {
        return calls.filter((entry) => entry.endsWith('/protected')).length === 1
          ? jsonResponse({ error: { code: 'AUTHENTICATION_REQUIRED', message: 'Expired.' } }, 401)
          : jsonResponse({ data: { ok: true } });
      }
      return jsonResponse({ data: { access_token: 'new-access', token_type: 'bearer' } });
    },
  });
  const response = await client.request('/protected');
  assert.deepEqual(response.data, { ok: true });
  assert.deepEqual(calls, ['/api/v1/protected', '/api/v1/auth/refresh', '/api/v1/protected']);
  assert.equal(store.getAccessToken(), 'new-access');
});

test('does not refresh auth endpoints', async () => {
  const store = createSessionStore(memoryStorage());
  store.saveTokens({ accessToken: 'access', refreshToken: 'refresh' });
  const calls = [];
  const client = createApiClient({ baseUrl: '/api/v1', session: store, fetchImpl: async (url) => {
    calls.push(url);
    return jsonResponse({ error: { code: 'INVALID_CREDENTIALS', message: 'Invalid.' } }, 401);
  } });
  await assert.rejects(() => client.request('/auth/login', { method: 'POST', body: {} }), (error) => error instanceof ApiError && error.code === 'INVALID_CREDENTIALS');
  assert.deepEqual(calls, ['/api/v1/auth/login']);
});

test('clears the session when refresh fails', async () => {
  const store = createSessionStore(memoryStorage());
  store.saveTokens({ accessToken: 'access', refreshToken: 'refresh' });
  let expired = false;
  const client = createApiClient({
    baseUrl: '/api/v1',
    session: store,
    onSessionExpired: () => { expired = true; },
    fetchImpl: async (url) => url.endsWith('/refresh')
      ? jsonResponse({ error: { code: 'INVALID_REFRESH_TOKEN', message: 'Expired.' } }, 401)
      : jsonResponse({ error: { code: 'AUTHENTICATION_REQUIRED', message: 'Expired.' } }, 401),
  });
  await assert.rejects(() => client.request('/protected'), (error) => error instanceof SessionExpiredError);
  assert.equal(expired, true);
  assert.equal(store.getAccessToken(), null);
  assert.equal(store.getRefreshToken(), null);
});
