import test from 'node:test';
import assert from 'node:assert/strict';
import { SESSION_STORAGE_KEY, createSessionStore } from '../src/api/sessionStore.js';

function fakeStorage(initial) {
  const values = new Map(initial ? [[SESSION_STORAGE_KEY, initial]] : []);
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

test('stores and normalizes snake-case token responses', () => {
  const store = createSessionStore(fakeStorage());
  store.saveTokens({ access_token: 'access', refresh_token: 'refresh' });
  assert.deepEqual(store.read(), { accessToken: 'access', refreshToken: 'refresh' });
  store.setAccessToken('new-access');
  assert.equal(store.getAccessToken(), 'new-access');
  assert.equal(store.getRefreshToken(), 'refresh');
});

test('clears corrupt storage instead of throwing', () => {
  const store = createSessionStore(fakeStorage('{not-json'));
  assert.deepEqual(store.read(), { accessToken: null, refreshToken: null });
  assert.equal(store.getAccessToken(), null);
});

test('clears both tokens on logout', () => {
  const store = createSessionStore(fakeStorage());
  store.saveTokens({ accessToken: 'access', refreshToken: 'refresh' });
  store.clear();
  assert.deepEqual(store.read(), { accessToken: null, refreshToken: null });
});
