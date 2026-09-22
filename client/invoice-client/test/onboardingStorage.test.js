import test from 'node:test';
import assert from 'node:assert/strict';
import { ONBOARDING_DRAFT_KEY, createOnboardingDraftStore } from '../src/onboarding/onboardingStorage.js';

function fakeStorage(initial = null) {
  const values = new Map(initial ? [[ONBOARDING_DRAFT_KEY, initial]] : []);
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

test('saves, restores, and clears onboarding drafts', () => {
  const store = createOnboardingDraftStore(fakeStorage());
  const draft = { business_name: 'Studio North', default_currency: 'KES' };
  store.save(draft);
  assert.deepEqual(store.read(), draft);
  store.clear();
  assert.equal(store.read(), null);
});

test('clears corrupt drafts instead of throwing', () => {
  const store = createOnboardingDraftStore(fakeStorage('{not-json'));
  assert.equal(store.read(), null);
});
