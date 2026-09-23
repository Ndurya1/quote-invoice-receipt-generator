import assert from 'node:assert/strict';
import test from 'node:test';
import { createApiClient } from '../src/api/apiClient.js';
import { SessionExpiredError } from '../src/api/apiErrors.js';
import { createSessionStore } from '../src/api/sessionStore.js';

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } });
}

function memoryStorage() {
  const values = new Map();
  return { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) };
}

test('coordinates one refresh across concurrent protected requests', async () => {
  const session = createSessionStore(memoryStorage());
  session.saveTokens({ accessToken: 'old-access', refreshToken: 'refresh-token' });
  let protectedCalls = 0;
  let refreshCalls = 0;
  const client = createApiClient({
    baseUrl: '/api/v1',
    session,
    fetchImpl: async (url) => {
      if (url.endsWith('/auth/refresh')) {
        refreshCalls += 1;
        await Promise.resolve();
        return jsonResponse({ data: { access_token: 'new-access', refresh_token: 'refresh-token' } });
      }
      protectedCalls += 1;
      return protectedCalls <= 2 ? jsonResponse({ error: { code: 'AUTHENTICATION_REQUIRED', message: 'Expired.' } }, 401) : jsonResponse({ data: { ok: true } });
    },
  });

  const [first, second] = await Promise.all([client.request('/protected'), client.request('/protected')]);
  assert.deepEqual(first.data, { ok: true });
  assert.deepEqual(second.data, { ok: true });
  assert.equal(refreshCalls, 1);
  assert.equal(protectedCalls, 4);
  assert.equal(session.getAccessToken(), 'new-access');
});

test('clears tokens and reports session expiry when refresh cannot recover', async () => {
  const session = createSessionStore(memoryStorage());
  session.saveTokens({ accessToken: 'access', refreshToken: 'refresh' });
  let expired = false;
  const client = createApiClient({
    baseUrl: '/api/v1',
    session,
    onSessionExpired: () => { expired = true; },
    fetchImpl: async (url) => url.endsWith('/auth/refresh')
      ? jsonResponse({ error: { code: 'INVALID_REFRESH_TOKEN', message: 'Expired.' } }, 401)
      : jsonResponse({ error: { code: 'AUTHENTICATION_REQUIRED', message: 'Expired.' } }, 401),
  });

  await assert.rejects(() => client.request('/protected'), (error) => error instanceof SessionExpiredError);
  assert.equal(expired, true);
  assert.equal(session.getAccessToken(), null);
  assert.equal(session.getRefreshToken(), null);
});
